import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';
import { navigateToRootStack } from '../utils/navigation';

const severityColors = {
  critical: colors.danger,
  high: colors.warning,
  medium: colors.primary,
  low: colors.ok,
};

export default function AlertCard({ alert, navigation }) {
  const alertId = alert.id || alert._id;
  const severityColor = severityColors[alert.severity] || colors.muted;
  const severityIcon =
    alert.severity === 'critical'
      ? 'warning'
      : alert.severity === 'high'
      ? 'alert-circle'
      : 'information-circle';

  return (
    <TouchableOpacity
      style={[styles.card, { borderLeftColor: severityColor }]}
      onPress={() => navigation.navigate('AlertDetail', { alertId: alert.id })}
    >
      <View style={styles.header}>
        <View style={[styles.severityBadge, { backgroundColor: severityColor + '20' }]}>
          <Ionicons name={severityIcon} size={16} color={severityColor} />
          <Text style={[styles.severityText, { color: severityColor }]}>
            {alert.severity?.toUpperCase() || 'UNKNOWN'}
          </Text>
        </View>
        {alert.device && (
          <Text style={styles.deviceName}>{alert.device.name || 'Unknown Device'}</Text>
        )}
      </View>
      <Text style={styles.message}>{alert.message || 'No message'}</Text>
      <Text style={styles.timestamp}>
        {new Date(alert.created_at || alert.createdAt).toLocaleString()}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 24,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  severityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  severityText: {
    fontSize: 12,
    fontWeight: '600',
  },
  deviceName: {
    fontSize: 12,
    color: colors.muted,
  },
  message: {
    fontSize: 16,
    color: colors.text,
    marginBottom: 8,
  },
  timestamp: {
    fontSize: 12,
    color: colors.muted,
  },
});
