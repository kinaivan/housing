import { useState, useEffect, useCallback, useMemo } from 'react';

interface Unit {
  id: number;
  occupants: number;
  rent: number;
  is_occupied: boolean;
}

interface Frame {
  units: Unit[];
  unhoused: number;
  year: number;
  period: number;
}

interface SimulationStats {
  totalUnits: number;
  occupiedUnits: number;
  averageRent: number;
  totalResidents: number;
}

const API_BASE = 'http://localhost:8000';

const useSimulation = () => {
  const [frame, setFrame] = useState<Frame | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'paused' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  // Compute derived state
  const isRunning = status === 'running';
  const isPaused = status === 'paused';

  // Process units data for the housing grid
  const units = useMemo(() => {
    if (!frame) return [];
    return frame.units || [];
  }, [frame]);

  // Calculate simulation statistics
  const stats = useMemo(() => {
    if (!frame) return {
      totalUnits: 0,
      occupiedUnits: 0,
      averageRent: 0,
      totalResidents: 0,
    };

    const totalUnits = frame.units?.length || 0;
    const occupiedUnits = frame.units?.filter(u => u.occupants > 0).length || 0;
    const totalRent = frame.units?.reduce((sum, u) => sum + u.rent, 0) || 0;
    const totalResidents = frame.units?.reduce((sum, u) => sum + u.occupants, 0) || 0;
    
    return {
      totalUnits,
      occupiedUnits,
      averageRent: totalUnits ? Math.round(totalRent / totalUnits) : 0,
      totalResidents,
    };
  }, [frame]);

  // WebSocket connection management
  const connectWebSocket = useCallback((newTaskId: string) => {
    if (ws) {
      ws.close();
    }

    const newWs = new WebSocket(`ws://localhost:8000/simulation/stream/${newTaskId}`);

    newWs.onopen = () => {
      console.log('WebSocket connected');
    };

    newWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'paused') {
          setStatus('paused');
        } else if (data.type === 'resumed') {
          setStatus('running');
        } else if (data.type === 'complete') {
          setStatus('idle');
          setTaskId(null);
        } else if (data.type === 'error') {
          setError(data.message);
          setStatus('error');
        } else {
          setFrame(data);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
        setError('Error parsing simulation data');
        setStatus('error');
      }
    };

    newWs.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('WebSocket connection error');
      setStatus('error');
    };

    newWs.onclose = () => {
      console.log('WebSocket closed');
      if (status === 'running') {
        setError('WebSocket connection closed unexpectedly');
        setStatus('error');
      }
    };

    setWs(newWs);
    return newWs;
  }, [ws, status]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
      if (taskId) {
        fetch(`${API_BASE}/simulation/stop/${taskId}`, { method: 'POST' }).catch(console.error);
      }
    };
  }, [ws, taskId]);

  // API actions
  const startSimulation = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/simulation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          initial_households: 20,
          migration_rate: 0.1,
          years: 10
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { simulation_id } = await response.json();
      setTaskId(simulation_id);
      setStatus('running');
      connectWebSocket(simulation_id);
    } catch (err) {
      console.error('Failed to start simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to start simulation');
      setStatus('error');
    }
  }, [connectWebSocket]);

  const pauseSimulation = useCallback(async () => {
    if (!taskId) return;
    try {
      const response = await fetch(`${API_BASE}/simulation/${taskId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'pause' })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setStatus('paused');
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
      setStatus('running');
    } catch (err) {
      console.error('Failed to resume simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to resume simulation');
      setStatus('error');
    }
  }, [taskId]);

  const resetSimulation = useCallback(async () => {
    if (!taskId) return;
    try {
      const response = await fetch(`${API_BASE}/simulation/${taskId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      setStatus('idle');
      setTaskId(null);
      if (ws) {
        ws.close();
      }
    } catch (err) {
      console.error('Failed to reset simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to reset simulation');
      setStatus('error');
    }
  }, [taskId, ws]);

  return {
    units,
    stats,
    isRunning,
    isPaused,
    error,
    status,
    startSimulation,
    pauseSimulation,
    resumeSimulation,
    resetSimulation,
  };
};

export default useSimulation; 