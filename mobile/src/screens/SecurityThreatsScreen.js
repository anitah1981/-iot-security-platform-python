import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, borderRadius } from '../theme';

export default function SecurityThreatsScreen({ navigation }) {
  const threats = [
    { icon: 'wifi-outline', title: 'WiFi jamming', desc: 'Detection of signal interference or jamming attempts' },
    { icon: 'people-outline', title: 'Unknown devices', desc: 'New or unidentified devices on your network' },
    { icon: 'warning-outline', title: 'IP changes', desc: 'Suspicious IP address changes on monitored devices' },
    { icon: 'lock-closed-outline', title: 'Credential attempts', desc: 'Failed login or brute-force detection' },
  ];
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Security Threats</Text>
        <Text style={styles.subtitle}>Types of threats Pro-Alert monitors and detects</Text>
      </View>
      <View style={styles.section}>
        {threats.map((t, i) => (
          <View key={i} style={styles.card}>
            <Ionicons name={t.icon} size={28} color={colors.primary} />
            <View style={styles.cardText}>
              <Text style={styles.cardTitle}>{t.title}</Text>
              <Text style={styles.cardDesc}>{t.desc}</Text>
            </View>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: { padding: spacing.lg },
  title: { fontSize: 28, fontWeight: '700', color: colors.text, marginBottom: 4 },
  subtitle: { fontSize: 15, color: colors.muted },
  section: { padding: spacing.lg },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    gap: spacing.md,
  },
  cardText: { flex: 1 },
  cardTitle: { fontSize: 16, fontWeight: '600', color: colors.text },
  cardDesc: { fontSize: 14, color: colors.muted, marginTop: 2 },
});
