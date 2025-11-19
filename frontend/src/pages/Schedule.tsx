import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSchedule, getTeams, setOverride, type Game, type Team } from '../lib/api';
import { ChevronLeft, ChevronRight, Save, RotateCcw, Calendar, CheckCircle2 } from 'lucide-react';
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
    const h = homeScore ? parseInt(homeScore) : undefined;
    const a = awayScore ? parseInt(awayScore) : undefined;
    
    overrideMutation.mutate({ 
      gameId: game.id, 
      homeScore: h, 
      awayScore: a, 
      isOverridden: true 
    });
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
          
          <div className="relative">
            <select
              value={week}
              onChange={(e) => setWeek(Number(e.target.value))}
              className="appearance-none bg-transparent text-white font-medium py-1 pl-2 pr-8 text-center outline-none cursor-pointer hover:text-blue-400 transition-colors"
            >
              {Array.from({ length: 18 }, (_, i) => i + 1).map((w) => (
                <option key={w} value={w} className="bg-[#1E1E1E] text-white">
                  Week {w}
                </option>
              ))}
            </select>
            <div className="absolute right-0 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
              <ChevronRight size={12} className="rotate-90" />
            </div>
          </div>

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
  const isCompleted = game.is_completed;

  return (
    <div className={clsx("bg-[#1E1E1E] rounded-lg p-4 border transition-colors relative overflow-hidden", 
      isEdited ? "border-blue-500/50 bg-blue-500/5" : "border-gray-800",
      isCompleted ? "opacity-75" : ""
    )}>
      {isCompleted && (
        <div className="absolute top-0 right-0 p-2">
           <CheckCircle2 size={16} className="text-green-500/50" />
        </div>
      )}
      
      <div className="flex justify-between items-center mb-4 text-sm text-gray-400">
        <div className="flex items-center gap-2">
          <Calendar size={14} />
          <span>{new Date(game.date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}</span>
        </div>
        {isEdited && <span className="text-blue-400 text-[10px] font-bold px-2 py-0.5 bg-blue-400/10 rounded uppercase tracking-wider">Override</span>}
      </div>
      
      <div className="space-y-4">
        {/* Away Team */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {awayTeam?.logo_url && <img src={awayTeam.logo_url} alt={awayTeam.abbreviation} className="w-8 h-8 object-contain" />}
            <div>
              <div className="font-bold text-lg text-white leading-none">{awayTeam?.abbreviation || game.away_team_id}</div>
              <div className="text-xs text-gray-500 mt-1">{awayTeam?.name}</div>
            </div>
          </div>
          <div className="flex flex-col gap-1 items-end">
            <input
              type="number"
              placeholder="Score"
              value={awayScore}
              onChange={(e) => setAwayScore(e.target.value)}
              className="w-16 bg-[#121212] border border-gray-700 rounded px-2 py-1 text-right text-white focus:border-blue-500 outline-none font-mono text-lg"
            />
          </div>
        </div>

        {/* Home Team */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {homeTeam?.logo_url && <img src={homeTeam.logo_url} alt={homeTeam.abbreviation} className="w-8 h-8 object-contain" />}
            <div>
              <div className="font-bold text-lg text-white leading-none">{homeTeam?.abbreviation || game.home_team_id}</div>
              <div className="text-xs text-gray-500 mt-1">{homeTeam?.name}</div>
            </div>
          </div>
          <div className="flex flex-col gap-1 items-end">
            <input
              type="number"
              placeholder="Score"
              value={homeScore}
              onChange={(e) => setHomeScore(e.target.value)}
              className="w-16 bg-[#121212] border border-gray-700 rounded px-2 py-1 text-right text-white focus:border-blue-500 outline-none font-mono text-lg"
            />
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end gap-2 pt-4 border-t border-gray-800/50">
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
