import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import api from '../config/api';
import { colors } from '../theme';

export default function AuditLogsScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setError(null);
      const res = await api.get('/api/audit/logs', { params: { limit: 50 } });
      setLogs(res.data?.logs || []);
    } catch (e) {
      const st = e.response?.status;
      if (st === 403) {
        setError('Audit logs are available on the Business plan. Open the web app to upgrade.');
      } else {
        const d = e.response?.data?.detail;
        setError(typeof d === 'string' ? d : 'Failed to load audit logs');
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
      <Text style={styles.title}>Audit Logs</Text>
      <Text style={styles.subtitle}>Activity history for your account</Text>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {logs.length === 0 ? (
        <Text style={styles.muted}>No audit logs yet.</Text>
      ) : (
        logs.map((log) => (
          <View key={log.id} style={styles.logCard}>
            <Text style={styles.logAction}>{log.action || 'Unknown'}</Text>
            <Text style={styles.muted}>{log.details || log.message || ''}</Text>
            <Text style={styles.logTime}>{log.createdAt ? new Date(log.createdAt).toLocaleString() : ''}</Text>
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
  logCard: { marginHorizontal: 24, padding: 16, backgroundColor: colors.card, borderRadius: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.border },
  logAction: { fontSize: 16, fontWeight: '600', color: colors.text },
  logTime: { fontSize: 12, color: colors.muted, marginTop: 8 },
  errorBox: { marginHorizontal: 24, padding: 16, backgroundColor: colors.danger + '20', borderRadius: 8 },
  errorText: { color: colors.danger },
  muted: { fontSize: 14, color: colors.muted },
});
