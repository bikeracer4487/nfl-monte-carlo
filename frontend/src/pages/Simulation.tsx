import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  getTeams,
  startSimulationJob,
  getSimulationJob,
  cancelSimulationJob,
  type SimulationResult,
  type Team,
  type TeamSimulationStats,
  type SimulationJob,
} from '../lib/api';
import { Play, Loader2, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import clsx from 'clsx';

type SortKey = 'team' | keyof Omit<TeamSimulationStats, 'seed_probabilities'>;
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  key: SortKey;
  direction: SortDirection;
}

export const Simulation = () => {
  const [numSimulations, setNumSimulations] = React.useState(10000);
  const [result, setResult] = React.useState<SimulationResult | null>(null);
  const [sortConfig, setSortConfig] = React.useState<SortConfig>({
    key: 'playoff_probability',
    direction: 'desc'
  });
  const [jobData, setJobData] = React.useState<SimulationJob | null>(null);
  const [jobId, setJobId] = React.useState<string | null>(null);
  const [jobError, setJobError] = React.useState<string | null>(null);
  const [isCancelling, setIsCancelling] = React.useState(false);

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: getTeams,
  });

  const teamMap = React.useMemo(() => {
    const map: Record<string, Team> = {};
    teams?.forEach(t => map[t.id] = t);
    return map;
  }, [teams]);

  const isJobActive = jobData?.status === 'pending' || jobData?.status === 'running';
  const progressValue = jobData ? jobData.progress ?? 0 : 0;

  const handleStartSimulation = async () => {
    if (isJobActive) return;
    try {
      setJobError(null);
      setResult(null);
      const job = await startSimulationJob(numSimulations);
      setJobData(job);
      setJobId(job.job_id);
    } catch (error) {
      setJobError('Failed to start simulation. Please try again.');
    }
  };

  const handleCancelSimulation = async () => {
    if (!jobData) return;
    try {
      setIsCancelling(true);
      const updated = await cancelSimulationJob(jobData.job_id);
      setJobData(updated);
    } catch (error) {
      setJobError('Failed to cancel simulation. Please try again.');
      setIsCancelling(false);
    }
  };

  React.useEffect(() => {
    if (!jobId) return;

    let active = true;

    const pollStatus = async () => {
      try {
        const latest = await getSimulationJob(jobId);
        if (!active) return;
        setJobData(latest);

        if (latest.status === 'completed') {
          setResult(latest.result ?? null);
          setJobId(null);
        } else if (latest.status === 'cancelled') {
          setJobId(null);
        } else if (latest.status === 'error') {
          setJobError(latest.error ?? 'Simulation failed.');
          setJobId(null);
        }
      } catch (error) {
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

  React.useEffect(() => {
    if (!jobData) return;
    if (jobData.status !== 'pending' && jobData.status !== 'running') {
      setIsCancelling(false);
    }
  }, [jobData]);

  const handleSort = (key: SortKey) => {
    setSortConfig(current => ({
      key,
      direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const sortedData = React.useMemo(() => {
    if (!result) return [];
    
    return Object.entries(result.team_stats).sort(([aId, aStats], [bId, bStats]) => {
      const direction = sortConfig.direction === 'asc' ? 1 : -1;
      
      if (sortConfig.key === 'team') {
        const aName = teamMap[aId]?.name || aId;
        const bName = teamMap[bId]?.name || bId;
        return aName.localeCompare(bName) * direction;
      }
      
      const aValue = aStats[sortConfig.key as keyof TeamSimulationStats];
      const bValue = bStats[sortConfig.key as keyof TeamSimulationStats];
      
      // Handle potential undefined values if types mismatch, though they shouldn't
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return (aValue - bValue) * direction;
      }
      return 0;
    });
  }, [result, sortConfig, teamMap]);

  const SortHeader = ({ label, sortKey }: { label: string, sortKey: SortKey }) => (
    <th 
      className="px-6 py-4 cursor-pointer hover:bg-[#2A2A2A] transition-colors select-none"
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center gap-2">
        {label}
        {sortConfig.key === sortKey ? (
          sortConfig.direction === 'asc' ? <ArrowUp size={16} className="text-blue-500" /> : <ArrowDown size={16} className="text-blue-500" />
        ) : (
          <ArrowUpDown size={16} className="text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity" />
        )}
      </div>
    </th>
  );

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6 text-white">Monte Carlo Simulation</h2>

      <div className="bg-[#1E1E1E] p-6 rounded-lg border border-gray-800 mb-8">
        <div className="flex flex-wrap items-end gap-4">
          <div className="flex-1 max-w-xs">
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Number of Simulations
            </label>
            <select
              value={numSimulations}
              onChange={(e) => setNumSimulations(Number(e.target.value))}
              className="w-full bg-[#121212] border border-gray-700 rounded px-3 py-2 text-white focus:border-blue-500 outline-none"
            >
              <option value={1000}>1,000 (Fast)</option>
              <option value={10000}>10,000 (Standard)</option>
              <option value={100000}>100,000 (High Precision)</option>
            </select>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={handleStartSimulation}
              disabled={isJobActive}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[180px] justify-center"
            >
              {isJobActive ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  Simulating...
                </>
              ) : (
                <>
                  <Play size={20} />
                  Run Simulation
                </>
              )}
            </button>
            {isJobActive && (
              <button
                onClick={handleCancelSimulation}
                disabled={isCancelling}
                className="px-4 py-2 rounded-lg border border-gray-700 text-gray-200 hover:border-red-500 hover:text-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCancelling ? 'Cancelling...' : 'Cancel'}
              </button>
            )}
          </div>
        </div>
      </div>

      {jobError && (
        <div className="mb-6 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {jobError}
        </div>
      )}

      {jobData && jobData.status !== 'completed' && (
        <div className="mb-8 bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 space-y-3">
          <div className="flex items-center gap-3">
            {isJobActive ? (
              <Loader2 className="text-blue-400 animate-spin" size={24} />
            ) : null}
            <div>
              <h3 className="font-semibold text-blue-400">
                {jobData.status === 'cancelled'
                  ? 'Simulation Cancelled'
                  : jobData.status === 'error'
                  ? 'Simulation Failed'
                  : 'Simulation In Progress'}
              </h3>
              <p className="text-sm text-gray-400">
                {jobData.message ||
                  `Status: ${jobData.status.charAt(0).toUpperCase()}${jobData.status.slice(1)}`}
              </p>
              {(jobData.status === 'pending' || jobData.status === 'running') && (
                <p className="text-xs text-gray-500 mt-1">
                  Running {jobData.num_simulations.toLocaleString()} simulations.{' '}
                  {jobData.num_simulations >= 100000
                    ? 'This may take a few minutes.'
                    : 'This may take a few seconds.'}
                </p>
              )}
            </div>
          </div>

          {(jobData.status === 'pending' || jobData.status === 'running') && (
            <div>
              <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                <span>Progress</span>
                <span>{progressValue}%</span>
              </div>
              <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${progressValue}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className="flex items-center justify-between text-sm text-gray-400">
            <span>Simulated {result.num_simulations.toLocaleString()} seasons in {result.execution_time.toFixed(2)}s</span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#1E1E1E]">
            <table className="w-full text-left text-sm">
              <thead className="bg-[#252525] text-gray-400 uppercase font-semibold">
                <tr className="group">
                  <SortHeader label="Team" sortKey="team" />
                  <SortHeader label="Avg Wins" sortKey="average_wins" />
                  <SortHeader label="Playoff %" sortKey="playoff_probability" />
                  <SortHeader label="Division %" sortKey="division_win_probability" />
                  <SortHeader label="#1 Seed %" sortKey="first_seed_probability" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {sortedData.map(([teamId, stats]) => {
                  const team = teamMap[teamId];
                  return (
                    <tr key={teamId} className="hover:bg-[#2A2A2A] transition-colors">
                      <td className="px-6 py-4 font-medium text-white flex items-center gap-3">
                        {team?.logo_url && <img src={team.logo_url} alt={team.abbreviation} className="w-6 h-6 object-contain" />}
                        {team?.name || teamId}
                      </td>
                      <td className="px-6 py-4 text-gray-300">{stats.average_wins.toFixed(1)}</td>
                      <td className="px-6 py-4">
                        <ProbabilityBar value={stats.playoff_probability} />
                      </td>
                      <td className="px-6 py-4">
                        <ProbabilityBar value={stats.division_win_probability} />
                      </td>
                      <td className="px-6 py-4">
                        <ProbabilityBar value={stats.first_seed_probability} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

const ProbabilityBar = ({ value }: { value: number }) => {
  const percentage = (value * 100).toFixed(1);
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={clsx("h-full rounded-full", 
            value > 0.8 ? "bg-green-500" : 
            value > 0.5 ? "bg-blue-500" : 
            value > 0.2 ? "bg-yellow-500" : "bg-red-500"
          )}
          style={{ width: `${value * 100}%` }}
        />
      </div>
      <span className="w-12 text-right text-gray-300 font-mono">{percentage}%</span>
    </div>
  );
};
