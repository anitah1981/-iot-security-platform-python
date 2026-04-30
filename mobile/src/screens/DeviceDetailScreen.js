import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../config/api';
import { colors } from '../theme';

export default function DeviceDetailScreen({ route }) {
  const { deviceId } = route?.params || {};
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (deviceId) {
      loadDevice();
    }
  }, [deviceId]);

  const loadDevice = async () => {
    try {
      const response = await api.get(
        `/api/devices/${encodeURIComponent(deviceId)}/status`
      );
      const d = response.data?.device;
      if (d) {
        setDevice({
          ...d,
          id: d.device_id,
          groups: d.groups || [],
        });
      } else {
        setDevice(null);
      }
    } catch (error) {
      console.error('Error loading device:', error);
      setDevice(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!device) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Device not found</Text>
      </View>
    );
  }

  const statusColor = device.status === 'online' ? colors.ok : colors.danger;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.statusIndicator}>
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
          <Text style={[styles.statusText, { color: statusColor }]}>
            {device.status?.toUpperCase() || 'UNKNOWN'}
          </Text>
        </View>
        <Text style={styles.deviceName}>{device.name || 'Unnamed Device'}</Text>
        <Text style={styles.deviceType}>{device.type || 'Unknown Type'}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Device Information</Text>
        <View style={styles.infoCard}>
          <InfoRow label="Device ID" value={device.device_id || device.id} />
          <InfoRow label="Type" value={device.type || 'N/A'} />
          <InfoRow label="Status" value={device.status || 'N/A'} />
          {device.last_seen && (
            <InfoRow
              label="Last Seen"
              value={new Date(device.last_seen).toLocaleString()}
            />
          )}
          {device.ip_address && <InfoRow label="IP Address" value={device.ip_address} />}
        </View>
      </View>

      {device.groups && device.groups.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Groups</Text>
          <View style={styles.groupsContainer}>
            {device.groups.map((group, index) => (
              <View key={index} style={styles.groupBadge}>
                <Text style={styles.groupText}>{group}</Text>
              </View>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );
}

function InfoRow({ label, value }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.bg,
  },
  errorText: {
    fontSize: 16,
    color: colors.danger,
  },
  header: {
    padding: 24,
    alignItems: 'center',
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 14,
    fontWeight: '600',
  },
  deviceName: {
    fontSize: 28,
    fontWeight: 'bold',
    color: colors.text,
    marginBottom: 8,
  },
  deviceType: {
    fontSize: 16,
    color: colors.muted,
  },
  section: {
    marginBottom: 24,
    paddingHorizontal: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text,
    marginBottom: 12,
  },
  infoCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  infoLabel: {
    fontSize: 14,
    color: colors.muted,
  },
  infoValue: {
    fontSize: 14,
    color: colors.text,
    fontWeight: '500',
  },
  groupsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  groupBadge: {
    backgroundColor: colors.primary,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  groupText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: '500',
  },
});
