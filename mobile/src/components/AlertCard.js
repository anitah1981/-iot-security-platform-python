import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const severityColors = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#3b82f6',
  low: '#10b981',
};

export default function AlertCard({ alert, navigation }) {
  const severityColor = severityColors[alert.severity] || '#666';
  const severityIcon =
    alert.severity === 'critical'
      ? 'warning'
      : alert.severity === 'high'
      ? 'alert-circle'
      : 'information-circle';

  return (
    <TouchableOpacity
      style={styles.card}
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
        {new Date(alert.created_at).toLocaleString()}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 24,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: severityColors.medium,
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
    color: '#999',
  },
  message: {
    fontSize: 16,
    color: '#ffffff',
    marginBottom: 8,
  },
  timestamp: {
    fontSize: 12,
    color: '#666',
  },
});
