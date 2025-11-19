import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getStandings, getTeams, type Team, type Standing } from '../lib/api';
import clsx from 'clsx';

type ViewMode = 'division' | 'conference' | 'league';

export const Standings = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('division');

  const { data: standings, isLoading: isLoadingStandings, error: standingsError } = useQuery({
    queryKey: ['standings'],
    queryFn: getStandings,
  });

  const { data: teams, isLoading: isLoadingTeams } = useQuery({
    queryKey: ['teams'],
    queryFn: getTeams,
  });

  const teamMap = useMemo(() => {
    const map: Record<string, Team> = {};
    teams?.forEach(t => map[t.id] = t);
    return map;
  }, [teams]);

  const groupedStandings = useMemo(() => {
    if (!standings || !teams) return null;

    if (viewMode === 'league') {
      return {
        title: 'League Standings',
        groups: [{
          name: 'NFL',
          teams: [...standings].sort((a, b) => b.win_percentage - a.win_percentage)
        }]
      };
    }

    if (viewMode === 'conference') {
      const afc = standings.filter(s => teamMap[s.team_id]?.conference === 'AFC')
        .sort((a, b) => b.win_percentage - a.win_percentage);
      const nfc = standings.filter(s => teamMap[s.team_id]?.conference === 'NFC')
        .sort((a, b) => b.win_percentage - a.win_percentage);
      
      return {
        title: 'Conference Standings',
        groups: [
          { name: 'AFC', teams: afc },
          { name: 'NFC', teams: nfc }
        ]
      };
    }

    // Division view
    const divisions = ['East', 'North', 'South', 'West'];
    const conferences = ['AFC', 'NFC'];
    const groups = [];

    for (const conf of conferences) {
      for (const div of divisions) {
        const divTeams = standings.filter(s => {
          const team = teamMap[s.team_id];
          return team?.conference === conf && team?.division === div;
        }).sort((a, b) => b.win_percentage - a.win_percentage);

        groups.push({ name: `${conf} ${div}`, teams: divTeams });
      }
    }

    return { title: 'Division Standings', groups };
  }, [standings, teams, teamMap, viewMode]);

  if (isLoadingStandings || isLoadingTeams) return <div className="p-8 text-gray-400">Loading data...</div>;
  if (standingsError) return <div className="p-8 text-red-500">Error loading standings. Is the backend running?</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Standings</h2>
        
        <div className="flex bg-[#1E1E1E] p-1 rounded-lg border border-gray-800">
          {(['division', 'conference', 'league'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={clsx(
                "px-4 py-1.5 rounded-md text-sm font-medium capitalize transition-colors",
                viewMode === mode 
                  ? "bg-[#252525] text-white shadow-sm" 
                  : "text-gray-400 hover:text-gray-200"
              )}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>
      
      <div className="space-y-8">
        {groupedStandings?.groups.map((group) => (
          <div key={group.name} className="rounded-lg border border-gray-800 bg-[#1E1E1E] overflow-hidden">
            <div className="bg-[#252525] px-6 py-3 border-b border-gray-800">
              <h3 className="font-bold text-gray-200">{group.name}</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-gray-400 uppercase font-semibold text-xs bg-[#1E1E1E]">
                  <tr>
                    <th className="px-6 py-3">Team</th>
                    <th className="px-4 py-3 text-center">W</th>
                    <th className="px-4 py-3 text-center">L</th>
                    <th className="px-4 py-3 text-center">T</th>
                    <th className="px-4 py-3 text-center">PCT</th>
                    <th className="px-4 py-3 text-center">DIV</th>
                    <th className="px-4 py-3 text-center">CONF</th>
                    <th className="px-4 py-3 text-center">PF</th>
                    <th className="px-4 py-3 text-center">PA</th>
                    <th className="px-4 py-3 text-center">DIFF</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {group.teams.map((stat) => {
                    const team = teamMap[stat.team_id];
                    return (
                      <tr key={stat.team_id} className="hover:bg-[#2A2A2A] transition-colors">
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-3">
                            {team?.logo_url && (
                              <img 
                                src={team.logo_url} 
                                alt={team.abbreviation} 
                                className="w-8 h-8 object-contain"
                              />
                            )}
                            <div className="flex flex-col">
                              <span className="font-bold text-white">{team?.display_name || stat.team_name}</span>
                              <span className="text-xs text-gray-500">{team?.abbreviation}</span>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center text-gray-300">{stat.wins}</td>
                        <td className="px-4 py-3 text-center text-gray-300">{stat.losses}</td>
                        <td className="px-4 py-3 text-center text-gray-300">{stat.ties}</td>
                        <td className="px-4 py-3 text-center text-gray-300">{stat.win_percentage.toFixed(3)}</td>
                        <td className="px-4 py-3 text-center text-gray-400">{stat.division_wins}-{stat.division_losses}-{stat.division_ties}</td>
                        <td className="px-4 py-3 text-center text-gray-400">{stat.conference_wins}-{stat.conference_losses}-{stat.conference_ties}</td>
                        <td className="px-4 py-3 text-center text-gray-300">{stat.points_for}</td>
                        <td className="px-4 py-3 text-center text-gray-300">{stat.points_against}</td>
                        <td className={clsx(
                          "px-4 py-3 text-center font-medium", 
                          stat.net_points > 0 ? "text-green-500" : stat.net_points < 0 ? "text-red-500" : "text-gray-400"
                        )}>
                          {stat.net_points > 0 ? "+" : ""}{stat.net_points}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

