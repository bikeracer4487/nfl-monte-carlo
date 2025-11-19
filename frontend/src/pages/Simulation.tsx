import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { runSimulation, getTeams, type SimulationResult, type Team, type TeamSimulationStats } from '../lib/api';
import { Play, Loader2, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import clsx from 'clsx';

type SortKey = 'team' | keyof Omit<TeamSimulationStats, 'seed_probabilities'>;
type SortDirection = 'asc' | 'desc';

interface SortConfig {
  key: SortKey;
  direction: SortDirection;
}

export const Simulation = () => {
  const [numSimulations, setNumSimulations] = useState(10000);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: 'playoff_probability',
    direction: 'desc'
  });

  const { data: teams } = useQuery({
    queryKey: ['teams'],
    queryFn: getTeams,
  });

  const teamMap = React.useMemo(() => {
    const map: Record<string, Team> = {};
    teams?.forEach(t => map[t.id] = t);
    return map;
  }, [teams]);

  const mutation = useMutation({
    mutationFn: () => runSimulation(numSimulations),
    onSuccess: (data) => {
      setResult(data);
    },
  });

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
        <div className="flex items-end gap-4">
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
          
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending ? (
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
        </div>
      </div>

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
