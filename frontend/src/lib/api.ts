import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export interface Team {
  id: string;
  abbreviation: string;
  name: string;
  display_name: string;
  location: string;
  conference: string;
  division: string;
  color?: string;
  logo_url?: string;
}

export interface Game {
  id: string;
  week: number;
  season: number;
  home_team_id: string;
  away_team_id: string;
  date: string;
  is_completed: boolean;
  home_score?: number;
  away_score?: number;
  home_moneyline?: number;
  away_moneyline?: number;
  home_win_probability?: number;
  away_win_probability?: number;
  is_overridden: boolean;
  override_home_score?: number;
  override_away_score?: number;
  override_home_moneyline?: number;
  override_away_moneyline?: number;
  last_updated?: string;
  odds_source?: string;
}

export interface Standing {
  team_id: string;
  team_name: string;
  wins: number;
  losses: number;
  ties: number;
  win_percentage: number;
  division_wins: number;
  division_losses: number;
  division_ties: number;
  conference_wins: number;
  conference_losses: number;
  conference_ties: number;
  points_for: number;
  points_against: number;
  net_points: number;
}

export interface SimulationResult {
  num_simulations: number;
  execution_time: number;
  team_stats: Record<string, TeamSimulationStats>;
}

export interface TeamSimulationStats {
  playoff_probability: number;
  division_win_probability: number;
  first_seed_probability: number;
  average_wins: number;
  seed_probabilities: Record<number, number>;
}

export type SimulationJobStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'cancelled'
  | 'error';

export interface SimulationJob {
  job_id: string;
  status: SimulationJobStatus;
  progress: number;
  message: string;
  num_simulations: number;
  random_seed?: number;
  result?: SimulationResult | null;
  error?: string;
  execution_time?: number;
  created_at?: number;
  started_at?: number;
  completed_at?: number;
}

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export const getTeams = async (): Promise<Team[]> => {
  const response = await api.get('/teams');
  return response.data;
};

export const getSchedule = async (week?: number): Promise<Game[]> => {
  const response = await api.get('/schedule', { params: { week } });
  return response.data;
};

export const getStandings = async (): Promise<Standing[]> => {
  const response = await api.get('/standings');
  return response.data;
};

export const runSimulation = async (
  numSimulations: number,
  randomSeed?: number
): Promise<SimulationResult> => {
  const payload: { num_simulations: number; random_seed?: number } = {
    num_simulations: numSimulations,
  };

  if (typeof randomSeed === 'number') {
    payload.random_seed = randomSeed;
  }

  const response = await api.post('/simulate', payload);
  return response.data;
};

export const setOverride = async (
  gameId: string, 
  homeScore?: number, 
  awayScore?: number, 
  isOverridden: boolean = true,
  homeMoneyline?: number,
  awayMoneyline?: number
): Promise<any> => {
  const response = await api.post('/override', {
    game_id: gameId,
    home_score: homeScore,
    away_score: awayScore,
    is_overridden: isOverridden,
    home_moneyline: homeMoneyline,
    away_moneyline: awayMoneyline
  });
  return response.data;
};

export const startSimulationJob = async (
  numSimulations: number,
  randomSeed?: number
): Promise<SimulationJob> => {
  const payload: { num_simulations: number; random_seed?: number } = {
    num_simulations: numSimulations,
  };

  if (typeof randomSeed === 'number') {
    payload.random_seed = randomSeed;
  }

  const response = await api.post('/simulation-jobs', payload);
  return response.data;
};

export const getSimulationJob = async (jobId: string): Promise<SimulationJob> => {
  const response = await api.get(`/simulation-jobs/${jobId}`);
  return response.data;
};

export async function cancelSimulationJob(jobId: string): Promise<SimulationJob> {
  const response = await api.delete(`/simulation-jobs/${jobId}`);
  return response.data;
}

