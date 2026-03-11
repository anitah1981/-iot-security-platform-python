import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, borderRadius } from '../theme';

export default function SecurityComplianceScreen({ navigation }) {
  const items = [
    { icon: 'shield-checkmark', title: 'MFA', desc: 'Multi-factor authentication for account security' },
    { icon: 'key', title: 'Encryption', desc: 'Data encrypted in transit and at rest' },
    { icon: 'document-text', title: 'Audit logs', desc: 'Full activity audit trail (Business plan)' },
    { icon: 'notifications', title: 'Alerts', desc: 'Multi-channel notifications (Email, SMS, WhatsApp, Voice)' },
  ];
  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Security & Compliance</Text>
        <Text style={styles.subtitle}>How Pro-Alert keeps your data and devices secure</Text>
      </View>
      <View style={styles.section}>
        {items.map((item, i) => (
          <View key={i} style={styles.card}>
            <Ionicons name={item.icon} size={28} color={colors.accent} />
            <View style={styles.cardText}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardDesc}>{item.desc}</Text>
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
