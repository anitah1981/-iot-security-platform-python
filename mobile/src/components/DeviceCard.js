import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';
import { navigateToRootStack } from '../utils/navigation';

export default function DeviceCard({ device, navigation }) {
  const statusColor = device.status === 'online' ? colors.ok : colors.danger;
  const statusIcon = device.status === 'online' ? 'checkmark-circle' : 'close-circle';

  const logicalId = device.device_id || device.deviceId;
  return (
    <TouchableOpacity
      style={styles.card}
      onPress={() =>
        logicalId &&
        navigateToRootStack(navigation, 'DeviceDetail', { deviceId: String(logicalId) })
      }
    >
      <View style={styles.header}>
        <View style={styles.deviceInfo}>
          <Text style={styles.deviceName}>{device.name || 'Unnamed Device'}</Text>
          <Text style={styles.deviceType}>{device.type || 'Unknown Type'}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: statusColor + '20' }]}>
          <Ionicons name={statusIcon} size={16} color={statusColor} />
          <Text style={[styles.statusText, { color: statusColor }]}>
            {device.status || 'unknown'}
          </Text>
        </View>
      </View>
      {device.last_seen && (
        <Text style={styles.lastSeen}>
          Last seen: {new Date(device.last_seen).toLocaleString()}
        </Text>
      )}
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
    borderWidth: 1,
    borderColor: colors.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  deviceInfo: {
    flex: 1,
  },
  deviceName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 4,
  },
  deviceType: {
    fontSize: 14,
    color: colors.muted,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  lastSeen: {
    fontSize: 12,
    color: colors.muted,
    marginTop: 8,
  },
});
