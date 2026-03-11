import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import api from '../config/api';
import { colors } from '../theme';

export default function FamilyScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [family, setFamily] = useState(null);
  const [members, setMembers] = useState([]);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setError(null);
      const [familyRes, membersRes] = await Promise.all([
        api.get('/api/family'),
        api.get('/api/family/members'),
      ]);
      setFamily(familyRes.data);
      setMembers(membersRes.data?.members || []);
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load family');
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
      <Text style={styles.title}>Family Sharing</Text>
      <Text style={styles.subtitle}>Manage family members and device access</Text>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {family && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>{family.name || 'My Family'}</Text>
          <Text style={styles.muted}>{members.length} member(s)</Text>
        </View>
      )}

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Members</Text>
        {members.length === 0 ? (
          <Text style={styles.muted}>No family members yet. Invite from the web app.</Text>
        ) : (
          members.map((m) => (
            <View key={m.id} style={styles.memberCard}>
              <Text style={styles.memberName}>{m.name || m.email}</Text>
              <Text style={styles.muted}>{m.email}</Text>
              <Text style={styles.role}>{m.role || 'member'}</Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  title: { fontSize: 24, fontWeight: '600', color: colors.text, marginHorizontal: 24, marginTop: 24 },
  subtitle: { fontSize: 14, color: colors.muted, marginHorizontal: 24, marginBottom: 24 },
  card: { marginHorizontal: 24, padding: 16, backgroundColor: colors.card, borderRadius: 12, marginBottom: 24, borderWidth: 1, borderColor: colors.border },
  cardTitle: { fontSize: 18, fontWeight: '600', color: colors.text },
  section: { marginHorizontal: 24, marginBottom: 24 },
  sectionTitle: { fontSize: 16, fontWeight: '600', color: colors.text, marginBottom: 12 },
  memberCard: { padding: 16, backgroundColor: colors.card, borderRadius: 12, marginBottom: 8, borderWidth: 1, borderColor: colors.border },
  memberName: { fontSize: 16, fontWeight: '600', color: colors.text },
  role: { fontSize: 12, color: colors.accent, marginTop: 4 },
  errorBox: { marginHorizontal: 24, padding: 16, backgroundColor: colors.danger + '20', borderRadius: 8 },
  errorText: { color: colors.danger },
  muted: { fontSize: 14, color: colors.muted },
});
