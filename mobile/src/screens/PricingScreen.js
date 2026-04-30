import React from 'react';
import { View, Text, StyleSheet, ScrollView, Linking } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { colors } from '../theme';

export default function PricingScreen() {
  const { apiUrl } = useAuth();
  const pricingUrl = apiUrl ? `${apiUrl.replace(/\/$/, '')}/pricing` : null;

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Pricing</Text>
      <Text style={styles.subtitle}>Pro-Alert plans for smart home security</Text>

      <View style={styles.planCard}>
        <Text style={styles.planName}>Free</Text>
        <Text style={styles.planPrice}>
          £0<Text style={styles.planPeriod}>/month</Text>
        </Text>
        <Text style={styles.planDesc}>Up to 5 devices, email alerts</Text>
      </View>

      <View style={[styles.planCard, styles.planPro]}>
        <Text style={styles.planName}>Pro</Text>
        <Text style={styles.planPrice}>
          £4.99<Text style={styles.planPeriod}>/month</Text>
        </Text>
        <Text style={styles.planDesc}>Up to 25 devices, SMS & WhatsApp</Text>
      </View>

      <View style={styles.planCard}>
        <Text style={styles.planName}>Business</Text>
        <Text style={styles.planPrice}>
          £9.99<Text style={styles.planPeriod}>/month</Text>
        </Text>
        <Text style={styles.planDesc}>Unlimited devices, teams, audit logs</Text>
      </View>

      {pricingUrl && (
        <Text
          style={styles.link}
          onPress={() => Linking.openURL(pricingUrl)}
        >
          <Ionicons name="open-outline" size={16} color={colors.primary} /> View full pricing on web
        </Text>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  title: { fontSize: 24, fontWeight: '600', color: colors.text, marginHorizontal: 24, marginTop: 24 },
  subtitle: { fontSize: 14, color: colors.muted, marginHorizontal: 24, marginBottom: 24 },
  planCard: { marginHorizontal: 24, padding: 20, backgroundColor: colors.card, borderRadius: 12, marginBottom: 16, borderWidth: 1, borderColor: colors.border },
  planPro: { borderColor: colors.primary, borderWidth: 2 },
  planName: { fontSize: 18, fontWeight: '600', color: colors.text },
  planPrice: { fontSize: 28, fontWeight: '700', color: colors.primary, marginTop: 8 },
  planPeriod: { fontSize: 14, fontWeight: '400', color: colors.muted },
  planDesc: { fontSize: 14, color: colors.muted, marginTop: 8 },
  link: { marginHorizontal: 24, marginTop: 16, color: colors.primary, fontSize: 14 },
});
