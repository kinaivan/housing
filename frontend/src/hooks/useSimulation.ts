import { useState, useEffect, useCallback, useMemo } from 'react';

interface Unit {
  id: number;
  occupants: number;
  rent: number;
  is_occupied: boolean;
  quality?: number;
  lastRenovation?: number;
  household?: {
    income: number;
    satisfaction: number;
    size: number;
  };
}

interface Frame {
  year: number;
  period: number;
  units: Unit[];
  metrics: {
    total_units: number;
    occupied_units: number;
    average_rent: number;
    total_population: number;
  };
}

interface SimulationStats {
  totalUnits: number;
  occupiedUnits: number;
  averageRent: number;
  totalResidents: number;
}

interface SimulationParams {
  initial_households?: number;
  migration_rate?: number;
  years?: number;
  rent_cap_enabled?: boolean;
}

const API_BASE = 'http://localhost:8000';

export default function useSimulation() {
  const [frame, setFrame] = useState<Frame | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'paused' | 'error'>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Compute stats from the current frame
  const stats = useMemo(() => ({
    totalUnits: frame?.metrics.total_units ?? 0,
    occupiedUnits: frame?.metrics.occupied_units ?? 0,
    averageRent: frame?.metrics.average_rent ?? 0,
    totalResidents: frame?.metrics.total_population ?? 0,
  }), [frame]);

  // Current simulation time
  const currentYear = frame?.year ?? 1;
  const currentPeriod = frame?.period ?? 1;

  // Process units data for the housing grid
  const units = useMemo(() => {
    if (!frame) return [];
    return frame.units;
  }, [frame]);

  // WebSocket connection management
  const connectWebSocket = useCallback((newTaskId: string) => {
    if (ws) {
      ws.close();
    }

    const newWs = new WebSocket(`ws://localhost:8000/simulation/stream/${newTaskId}`);
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 3;
    const reconnectDelay = 1000; // 1 second

    const reconnect = () => {
      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        setTimeout(() => {
          console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
          connectWebSocket(newTaskId);
        }, reconnectDelay * reconnectAttempts);
      } else {
        setError('Failed to connect to simulation server after multiple attempts');
        setStatus('error');
      }
    };

    newWs.onopen = () => {
      console.log('WebSocket connected');
      reconnectAttempts = 0; // Reset reconnect attempts on successful connection
    };

    newWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'paused') {
          setIsPaused(true);
          setStatus('paused');
          setIsRunning(false);
        } else if (data.type === 'resumed') {
          setIsPaused(false);
          setStatus('running');
          setIsRunning(true);
        } else if (data.type === 'complete') {
          setIsPaused(false);
          setIsRunning(false);
          setStatus('idle');
          setTaskId(null);
        } else if (data.type === 'error') {
          setError(data.message);
          setStatus('error');
          setIsRunning(false);
          setIsPaused(false);
        } else {
          setFrame(data);
          setError(null); // Clear any previous errors
          // Don't automatically change state - only explicit control messages should do that
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        setError('Error parsing simulation data');
        setStatus('error');
        setIsRunning(false);
        setIsPaused(false);
      }
    };

    newWs.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('WebSocket connection error');
      setStatus('error');
      reconnect();
    };

    newWs.onclose = (event) => {
      console.log('WebSocket closed', event.code, event.reason);
      // Only treat as unexpected if we're actively running and it wasn't a clean close
      if ((status === 'running' || isRunning) && event.code !== 1000) {
        setError('WebSocket connection closed unexpectedly');
        setStatus('error');
        reconnect();
      }
    };

    setWs(newWs);
    return newWs;
  }, [ws, status, isRunning]);

  // Synchronize isRunning with status
  useEffect(() => {
    if (status === 'running' && !isRunning && !isPaused) {
      setIsRunning(true);
    } else if (status === 'paused' && isRunning) {
      setIsRunning(false);
    } else if (status === 'idle' && (isRunning || isPaused)) {
      setIsRunning(false);
      setIsPaused(false);
    }
  }, [status, isRunning, isPaused]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
      if (taskId) {
        fetch(`${API_BASE}/simulation/${taskId}/control`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'reset' })
        }).catch(console.error);
      }
    };
  }, [ws, taskId]);

  // API actions
  const startSimulation = useCallback(async (params: SimulationParams = {}) => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/simulation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          initial_households: params.initial_households ?? 20,
          migration_rate: params.migration_rate ?? 0.1,
          years: params.years ?? 10,
          rent_cap_enabled: params.rent_cap_enabled ?? false,
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { simulation_id } = await response.json();
      setTaskId(simulation_id);
      setStatus('running');
      setIsRunning(true);  // Set isRunning to true when starting
      setIsPaused(false);  // Make sure paused is false
      connectWebSocket(simulation_id);
    } catch (err) {
      console.error('Failed to start simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to start simulation');
      setStatus('error');
      throw err; // Re-throw to handle in the component
    }
  }, [connectWebSocket]);

  const pauseSimulation = useCallback(async () => {
    if (!taskId) {
      console.log('No taskId available for pause');
      return;
    }
    try {
      console.log('Sending pause signal for task:', taskId);
      const response = await fetch(`${API_BASE}/simulation/${taskId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'pause' })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      console.log('Pause signal sent successfully');
      setIsPaused(true);
      setStatus('paused');
      setIsRunning(false);
    } catch (err) {
      console.error('Failed to pause simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to pause simulation');
      setStatus('error');
    }
  }, [taskId]);

  const resumeSimulation = useCallback(async () => {
    if (!taskId) return;
    try {
      const response = await fetch(`${API_BASE}/simulation/${taskId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'resume' })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setIsPaused(false);
      setStatus('running');
      setIsRunning(true);
    } catch (err) {
      console.error('Failed to resume simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to resume simulation');
      setStatus('error');
    }
  }, [taskId]);

  const resetSimulation = useCallback(async () => {
    try {
      // Reset local state first
      setIsRunning(false);
      setIsPaused(false);
      setFrame(null);
      setError(null);
      setStatus('idle');
      
      // Close WebSocket connection
      if (ws) {
        ws.close();
        setWs(null);
      }
      
      // Send reset signal to backend if there's an active task
      if (taskId) {
        const response = await fetch(`${API_BASE}/simulation/${taskId}/control`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'reset' })
        });
        if (!response.ok) {
          console.warn(`Reset request failed with status: ${response.status}`);
        }
      }
      
      // Clear task ID last
      setTaskId(null);
    } catch (err) {
      console.error('Failed to reset simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to reset simulation');
      setStatus('error');
    }
  }, [taskId, ws]);

  const seekToStep = useCallback(async (step: number) => {
    if (!taskId) return;
    try {
      const response = await fetch(`${API_BASE}/simulation/${taskId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'seek', step })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (err) {
      console.error('Failed to seek simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to seek simulation');
      setStatus('error');
    }
  }, [taskId]);

  // Update the processMessage function to handle the new data
  const processMessage = useCallback((message: string) => {
    try {
      const data = JSON.parse(message);

      if (data.type === 'error') {
        setError(data.message);
        setStatus('error');
        setIsRunning(false);
        return;
      }

      if (data.type === 'complete') {
        setIsRunning(false);
        setStatus('idle');
        return;
      }

      if (data.type === 'paused') {
        console.log('Received paused message from backend');
        setIsPaused(true);
        setStatus('paused');
        setIsRunning(false);
        return;
      }

      if (data.type === 'resumed') {
        console.log('Received resumed message from backend');
        setIsPaused(false);
        setStatus('running');
        setIsRunning(true);
        return;
      }

      // Regular frame update
      setFrame(data);
      setError(null);
      // Don't automatically set status to running - preserve paused state

    } catch (e) {
      console.error('Error processing message:', e);
      setError('Error processing simulation data');
      setStatus('error');
    }
  }, []);

  return {
    units,
    frame,
    stats,
    isRunning,
    isPaused,
    error,
    status,
    currentYear,
    currentPeriod,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    resetSimulation,
    seekToStep,
  };
} 