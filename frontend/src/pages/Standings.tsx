import { useQuery } from '@tanstack/react-query';
import { getStandings } from '../lib/api';
import clsx from 'clsx';

export const Standings = () => {
  const { data: standings, isLoading, error } = useQuery({
    queryKey: ['standings'],
    queryFn: getStandings,
  });

  if (isLoading) return <div className="p-8 text-gray-400">Loading standings...</div>;
  if (error) return <div className="p-8 text-red-500">Error loading standings. Is the backend running?</div>;

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-6 text-white">NFL Standings</h2>
      
      <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#1E1E1E]">
        <table className="w-full text-left text-sm">
          <thead className="bg-[#252525] text-gray-400 uppercase font-semibold">
            <tr>
              <th className="px-6 py-4">Team</th>
              <th className="px-6 py-4">W</th>
              <th className="px-6 py-4">L</th>
              <th className="px-6 py-4">T</th>
              <th className="px-6 py-4">PCT</th>
              <th className="px-6 py-4">DIV</th>
              <th className="px-6 py-4">CONF</th>
              <th className="px-6 py-4">PF</th>
              <th className="px-6 py-4">PA</th>
              <th className="px-6 py-4">DIFF</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {standings?.map((team) => (
              <tr key={team.team_id} className="hover:bg-[#2A2A2A] transition-colors">
                <td className="px-6 py-4 font-medium text-white">{team.team_name}</td>
                <td className="px-6 py-4 text-gray-300">{team.wins}</td>
                <td className="px-6 py-4 text-gray-300">{team.losses}</td>
                <td className="px-6 py-4 text-gray-300">{team.ties}</td>
                <td className="px-6 py-4 text-gray-300">{team.win_percentage.toFixed(3)}</td>
                <td className="px-6 py-4 text-gray-400">{team.division_wins}-{team.division_losses}-{team.division_ties}</td>
                <td className="px-6 py-4 text-gray-400">{team.conference_wins}-{team.conference_losses}-{team.conference_ties}</td>
                <td className="px-6 py-4 text-gray-300">{team.points_for}</td>
                <td className="px-6 py-4 text-gray-300">{team.points_against}</td>
                <td className={clsx("px-6 py-4 font-medium", team.net_points > 0 ? "text-green-500" : team.net_points < 0 ? "text-red-500" : "text-gray-400")}>
                  {team.net_points > 0 ? "+" : ""}{team.net_points}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
