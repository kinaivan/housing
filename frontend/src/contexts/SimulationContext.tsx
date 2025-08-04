import React, { createContext, useContext, useCallback, useState, useEffect, useMemo, useRef } from 'react';

interface Unit {
  id: number;
  occupants: number;
  rent: number;
  is_occupied: boolean;
  is_owner_occupied: boolean;
  quality?: number;
  lastRenovation?: number;
  household?: {
    id: number;
    name: string;
    age: number;
    size: number;
    income: number;
    wealth: number;
    satisfaction: number;
    life_stage: string;
    monthly_payment?: number;
    mortgage_balance?: number;
    mortgage_interest_rate?: number;
    mortgage_term?: number;
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
    policy_metrics?: {
      total_lvt_collected?: number;
      violations_found?: number;
      improvements_required?: number;
      lvt_rate?: number;
    };
  };
  moves?: Array<{
    household_id: number;
    household_name: string;
    from_unit_id: number | null;
    to_unit_id: number | null;
    type?: string;
  }>;
  events?: Array<{
    type: string;
    household_id: number;
    household_name: string;
    from_unit_id?: number | null;
    to_unit_id?: number | null;
    reason?: string;
    rent_burden?: number;
    original_size?: number;
    remaining_size?: number;
    new_household_id?: number;
    new_household_size?: number;
    other_household_id?: number;
    other_household_size?: number;
    combined_size?: number;
  }>;
  unhoused_households?: Array<{
    id: number;
    name: string;
    size: number;
    income: number;
    wealth: number;
  }>;
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
  lvt_enabled?: boolean;
  lvt_rate?: number;
}

interface SimulationContextType {
  frame: Frame | null;
  units: Unit[];
  stats: SimulationStats;
  isRunning: boolean;
  isPaused: boolean;
  error: string | null;
  status: 'idle' | 'running' | 'paused' | 'error';
  currentYear: number;
  currentPeriod: number;
  startSimulation: (params?: SimulationParams) => Promise<void>;
  pauseSimulation: () => Promise<void>;
  resumeSimulation: () => Promise<void>;
  resetSimulation: () => Promise<void>;
  seekToStep: (step: number) => Promise<void>;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

const API_BASE = 'http://localhost:8000';

export const SimulationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [frame, setFrame] = useState<Frame | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'running' | 'paused' | 'error'>('idle');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [ws]);

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
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
          connectWebSocket(newTaskId);
        }, reconnectDelay * reconnectAttempts);
      } else {
        setError('Failed to connect to simulation server after multiple attempts');
        setStatus('error');
        setIsRunning(false);
        setIsPaused(false);
      }
    };

    newWs.onopen = () => {
      console.log('WebSocket connected');
      reconnectAttempts = 0; // Reset reconnect attempts on successful connection
      setError(null);
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
          if (ws) {
            ws.close();
          }
        } else if (data.type === 'error') {
          setError(data.message);
          setStatus('error');
          setIsRunning(false);
          setIsPaused(false);
        } else {
          // Log frame data for debugging
          console.log('Frame data:', {
            year: data.year,
            period: data.period,
            moves: data.moves,
            policy_metrics: data.metrics?.policy_metrics,
          });
          setFrame(data);
          setError(null);
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
      setIsRunning(true);
      setIsPaused(false);
      connectWebSocket(simulation_id);
    } catch (err) {
      console.error('Failed to start simulation:', err);
      setError(err instanceof Error ? err.message : 'Failed to start simulation');
      setStatus('error');
      throw err;
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

  const value: SimulationContextType = {
    frame,
    units,
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

  return (
    <SimulationContext.Provider value={value}>
      {children}
    </SimulationContext.Provider>
  );
};

export const useSimulation = () => {
  const context = useContext(SimulationContext);
  if (context === undefined) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
};

export default useSimulation; 