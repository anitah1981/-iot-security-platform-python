import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import api from '../config/api';
import { colors } from '../theme';

export default function IncidentsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [incidents, setIncidents] = useState([]);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setError(null);
      const res = await api.get('/api/incidents');
      setIncidents(res.data?.incidents || []);
    } catch (e) {
      const st = e.response?.status;
      const detail = e.response?.data?.detail;
      const msg =
        typeof detail === 'string'
          ? detail
          : Array.isArray(detail)
            ? detail.map((x) => x.msg || x).join(', ')
            : 'Failed to load incidents';
      if (st === 403) {
        setError(
          'Incidents need a Pro or Business plan. Upgrade on the web app, or use Alerts for all users.'
        );
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <Text style={styles.muted}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.primary} />}
    >
      <Text style={styles.title}>Incidents</Text>
      <Text style={styles.subtitle}>Security incidents and investigations</Text>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {incidents.length === 0 ? (
        <Text style={styles.muted}>No incidents recorded.</Text>
      ) : (
        incidents.map((i) => (
          <View key={i.id} style={styles.card}>
            <Text style={styles.cardTitle}>{i.title || i.type || 'Incident'}</Text>
            <Text style={styles.muted}>{i.description || i.summary || ''}</Text>
            <Text style={styles.time}>{i.createdAt ? new Date(i.createdAt).toLocaleString() : ''}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  title: { fontSize: 24, fontWeight: '600', color: colors.text, marginHorizontal: 24, marginTop: 24 },
  subtitle: { fontSize: 14, color: colors.muted, marginHorizontal: 24, marginBottom: 24 },
  card: { marginHorizontal: 24, padding: 16, backgroundColor: colors.card, borderRadius: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.border },
  cardTitle: { fontSize: 16, fontWeight: '600', color: colors.text },
  time: { fontSize: 12, color: colors.muted, marginTop: 8 },
  errorBox: { marginHorizontal: 24, padding: 16, backgroundColor: colors.danger + '20', borderRadius: 8 },
  errorText: { color: colors.danger },
  muted: { fontSize: 14, color: colors.muted },
});
