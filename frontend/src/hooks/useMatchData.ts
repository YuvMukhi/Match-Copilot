import { useEffect, useState, useCallback } from 'react';
import { api } from '../services/api';
import type { MatchState, MatchSummary, TeamDetail, TeamSummary } from '../types';

export function useMatchData() {
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [teams, setTeams] = useState<TeamSummary[]>([]);
  const [selectedMatchId, setSelectedMatchId] = useState<string>('match_001');
  const [selectedTeamId, setSelectedTeamId] = useState<string>('team_001');
  const [currentOver, setCurrentOver] = useState<number>(10);
  
  const [matchState, setMatchState] = useState<MatchState | null>(null);
  const [teamDetail, setTeamDetail] = useState<TeamDetail | null>(null);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initial load of matches and teams
  useEffect(() => {
    let mounted = true;
    async function init() {
      try {
        setLoading(true);
        setError(null);
        const [matchesData, teamsData] = await Promise.all([
          api.getMatches(),
          api.getTeams(),
        ]);
        if (mounted) {
          setMatches(matchesData);
          setTeams(teamsData);
          if (matchesData.length > 0) {
            setSelectedMatchId(matchesData[0].id);
          }
          if (teamsData.length > 0) {
            setSelectedTeamId(teamsData[0].id);
          }
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load initial match data');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    void init();
    return () => {
      mounted = false;
    };
  }, []);

  // Fetch updated match state and team detail whenever match, team, or over changes
  const refreshState = useCallback(async () => {
    if (!selectedMatchId || !selectedTeamId) return;
    try {
      setError(null);
      const [stateData, teamData] = await Promise.all([
        api.getMatchState(selectedMatchId, currentOver, selectedTeamId),
        api.getTeamDetail(selectedTeamId, currentOver),
      ]);
      setMatchState(stateData);
      setTeamDetail(teamData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update live match moment');
    }
  }, [selectedMatchId, selectedTeamId, currentOver]);

  useEffect(() => {
    void refreshState();
  }, [refreshState]);

  return {
    matches,
    teams,
    selectedMatchId,
    setSelectedMatchId,
    selectedTeamId,
    setSelectedTeamId,
    currentOver,
    setCurrentOver,
    matchState,
    teamDetail,
    loading,
    error,
    refreshState,
  };
}
