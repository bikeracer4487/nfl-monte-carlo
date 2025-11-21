import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  startSimulationJob,
  getSimulationJob,
  cancelSimulationJob,
  type SimulationResult,
  type SimulationJob,
} from '../lib/api';

interface SimulationContextType {
  result: SimulationResult | null;
  jobData: SimulationJob | null;
  jobId: string | null;
  jobError: string | null;
  isCancelling: boolean;
  simulatedAt: Date | null;
  startSimulation: (numSimulations: number) => Promise<void>;
  cancelSimulation: () => Promise<void>;
  clearResult: () => void;
}

const SimulationContext = createContext<SimulationContextType | undefined>(undefined);

export const useSimulation = () => {
  const context = useContext(SimulationContext);
  if (!context) {
    throw new Error('useSimulation must be used within a SimulationProvider');
  }
  return context;
};

export const SimulationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [jobData, setJobData] = useState<SimulationJob | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);
  const [simulatedAt, setSimulatedAt] = useState<Date | null>(null);

  const clearResult = useCallback(() => {
      setResult(null);
      setSimulatedAt(null);
  }, []);

  const startSimulation = useCallback(async (numSimulations: number) => {
    if (jobData?.status === 'pending' || jobData?.status === 'running') return;
    try {
      setJobError(null);
      // Don't clear previous result immediately if we want to show it while new one runs?
      // Requirement says: "persist until the user initiates a new simulation"
      // So we should probably clear it when starting a new one.
      setResult(null); 
      setSimulatedAt(null);
      
      const job = await startSimulationJob(numSimulations);
      setJobData(job);
      setJobId(job.job_id);
    } catch {
      setJobError('Failed to start simulation. Please try again.');
    }
  }, [jobData]);

  const cancelSimulation = useCallback(async () => {
    if (!jobData) return;
    try {
      setIsCancelling(true);
      const updated = await cancelSimulationJob(jobData.job_id);
      setJobData(updated);
    } catch {
      setJobError('Failed to cancel simulation. Please try again.');
      setIsCancelling(false);
    }
  }, [jobData]);

  useEffect(() => {
    if (!jobId) return;

    let active = true;
    const pollStatus = async () => {
      try {
        const latest = await getSimulationJob(jobId);
        if (!active) return;
        setJobData(latest);

        if (latest.status === 'completed') {
          setResult(latest.result ?? null);
          setSimulatedAt(new Date());
          setJobId(null);
        } else if (latest.status === 'cancelled') {
          setJobId(null);
        } else if (latest.status === 'error') {
          setJobError(latest.error ?? 'Simulation failed.');
          setJobId(null);
        }
      } catch {
        if (!active) return;
        setJobError('Failed to fetch simulation progress.');
        setJobId(null);
      }
    };

    pollStatus();
    const intervalId = window.setInterval(pollStatus, 1000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [jobId]);

  useEffect(() => {
    if (!jobData) return;
    if (jobData.status !== 'pending' && jobData.status !== 'running') {
      setIsCancelling(false);
    }
  }, [jobData]);

  return (
    <SimulationContext.Provider
      value={{
        result,
        jobData,
        jobId,
        jobError,
        isCancelling,
        simulatedAt,
        startSimulation,
        cancelSimulation,
        clearResult
      }}
    >
      {children}
    </SimulationContext.Provider>
  );
};

