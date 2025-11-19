import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSchedule, getTeams, setOverride, type Game, type Team } from '../lib/api';
import { ChevronLeft, ChevronRight, Save, RotateCcw } from 'lucide-react';
import clsx from 'clsx';

export const Schedule = () => {
  const [week, setWeek] = useState(1);
  const queryClient = useQueryClient();

  const { data: games, isLoading: isLoadingGames } = useQuery({
    queryKey: ['schedule', week],
    queryFn: () => getSchedule(week),
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

  const overrideMutation = useMutation({
    mutationFn: ({ gameId, homeScore, awayScore, isOverridden }: { gameId: string; homeScore?: number; awayScore?: number; isOverridden: boolean }) =>
      setOverride(gameId, homeScore, awayScore, isOverridden),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedule'] });
    },
  });

  const handleOverride = (game: Game, homeScore: string, awayScore: string) => {
    const h = parseInt(homeScore);
    const a = parseInt(awayScore);
    if (!isNaN(h) && !isNaN(a)) {
      overrideMutation.mutate({ gameId: game.id, homeScore: h, awayScore: a, isOverridden: true });
    }
  };

  const clearOverride = (gameId: string) => {
    overrideMutation.mutate({ gameId: gameId, isOverridden: false });
  };

  if (isLoadingGames) return <div className="p-8 text-gray-400">Loading schedule...</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Schedule</h2>
        <div className="flex items-center gap-4 bg-[#1E1E1E] rounded-lg p-1 border border-gray-800">
          <button
            onClick={() => setWeek(w => Math.max(1, w - 1))}
            className="p-2 hover:bg-gray-700 rounded-md text-gray-400 hover:text-white disabled:opacity-50"
            disabled={week === 1}
          >
            <ChevronLeft size={20} />
          </button>
          <span className="font-medium text-white min-w-[80px] text-center">Week {week}</span>
          <button
            onClick={() => setWeek(w => Math.min(18, w + 1))}
            className="p-2 hover:bg-gray-700 rounded-md text-gray-400 hover:text-white disabled:opacity-50"
            disabled={week === 18}
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {games?.map((game) => (
          <GameCard 
            key={game.id} 
            game={game} 
            teamMap={teamMap}
            onSave={(h, a) => handleOverride(game, h, a)}
            onClear={() => clearOverride(game.id)}
          />
        ))}
      </div>
    </div>
  );
};

const GameCard = ({ game, teamMap, onSave, onClear }: { game: Game; teamMap: Record<string, Team>; onSave: (h: string, a: string) => void; onClear: () => void }) => {
  const [homeScore, setHomeScore] = useState(game.override_home_score?.toString() || game.home_score?.toString() || '');
  const [awayScore, setAwayScore] = useState(game.override_away_score?.toString() || game.away_score?.toString() || '');
  
  React.useEffect(() => {
      if (game.is_overridden) {
          setHomeScore(game.override_home_score?.toString() || '');
          setAwayScore(game.override_away_score?.toString() || '');
      } else {
          setHomeScore(game.home_score?.toString() || '');
          setAwayScore(game.away_score?.toString() || '');
      }
  }, [game]);

  const isEdited = game.is_overridden;
  const homeTeam = teamMap[game.home_team_id];
  const awayTeam = teamMap[game.away_team_id];

  return (
    <div className={clsx("bg-[#1E1E1E] rounded-lg p-4 border transition-colors", isEdited ? "border-blue-500/50 bg-blue-500/5" : "border-gray-800")}>
      <div className="flex justify-between items-center mb-4 text-sm text-gray-400">
        <span>{new Date(game.date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</span>
        {isEdited && <span className="text-blue-400 text-[10px] font-bold px-2 py-0.5 bg-blue-400/10 rounded uppercase tracking-wider">Override</span>}
      </div>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {awayTeam?.logo_url && <img src={awayTeam.logo_url} alt={awayTeam.abbreviation} className="w-8 h-8 object-contain" />}
            <span className="font-bold text-lg text-white">{awayTeam?.name || game.away_team_id}</span>
          </div>
          <input
            type="number"
            value={awayScore}
            onChange={(e) => setAwayScore(e.target.value)}
            className="w-16 bg-[#121212] border border-gray-700 rounded px-2 py-1 text-right text-white focus:border-blue-500 outline-none font-mono"
          />
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {homeTeam?.logo_url && <img src={homeTeam.logo_url} alt={homeTeam.abbreviation} className="w-8 h-8 object-contain" />}
            <span className="font-bold text-lg text-white">{homeTeam?.name || game.home_team_id}</span>
          </div>
          <input
            type="number"
            value={homeScore}
            onChange={(e) => setHomeScore(e.target.value)}
            className="w-16 bg-[#121212] border border-gray-700 rounded px-2 py-1 text-right text-white focus:border-blue-500 outline-none font-mono"
          />
        </div>
      </div>

      <div className="mt-4 flex justify-end gap-2">
        {isEdited && (
          <button
            onClick={onClear}
            className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded transition-colors"
            title="Clear Override"
          >
            <RotateCcw size={18} />
          </button>
        )}
        <button
          onClick={() => onSave(homeScore, awayScore)}
          className={clsx(
            "p-2 rounded transition-colors",
            isEdited 
              ? "text-blue-400 hover:bg-blue-400/10" 
              : "text-gray-400 hover:text-blue-400 hover:bg-blue-400/10"
          )}
          title="Save Override"
        >
          <Save size={18} />
        </button>
      </div>
    </div>
  );
};
