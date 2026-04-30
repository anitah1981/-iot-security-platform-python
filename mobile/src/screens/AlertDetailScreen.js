import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../config/api';
import { colors } from '../theme';

const severityColors = {
  critical: colors.danger,
  high: colors.warning,
  medium: colors.primary,
  low: colors.ok,
};

export default function AlertDetailScreen({ route }) {
  const { alertId } = route?.params || {};
  const [alert, setAlert] = useState(null);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);

  useEffect(() => {
    if (alertId) {
      loadAlert();
    }
  }, [alertId]);

  const loadAlert = async () => {
    try {
      const response = await api.get(`/api/alerts/${alertId}`);
      setAlert(response.data);
    } catch (error) {
      console.error('Error loading alert:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!alert || alert.resolved) return;

    setResolving(true);
    try {
      await api.post(`/api/alerts/${alertId}/resolve`);
      Alert.alert('Resolved', 'This alert was marked as resolved.');
      await loadAlert();
    } catch (error) {
      const msg = error.response?.data?.detail;
      Alert.alert(
        'Could not resolve',
        typeof msg === 'string' ? msg : 'Please try again.'
      );
    } finally {
      setResolving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (!alert) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorText}>Alert not found</Text>
      </View>
    );
  }

  const severityColor = severityColors[alert.severity] || colors.muted;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={[styles.severityBadge, { backgroundColor: severityColor + '20' }]}>
          <Ionicons
            name={
              alert.severity === 'critical'
                ? 'warning'
                : alert.severity === 'high'
                ? 'alert-circle'
                : 'information-circle'
            }
            size={24}
            color={severityColor}
          />
          <Text style={[styles.severityText, { color: severityColor }]}>
            {alert.severity?.toUpperCase() || 'UNKNOWN'}
          </Text>
        </View>
        <Text style={styles.alertMessage}>{alert.message || 'No message'}</Text>
        <Text style={styles.alertType}>Type: {alert.type || 'N/A'}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Alert Information</Text>
        <View style={styles.infoCard}>
          <InfoRow label="Status" value={alert.resolved ? 'Resolved' : 'Active'} />
          <InfoRow
            label="Created"
            value={new Date(alert.created_at).toLocaleString()}
          />
          {alert.resolved_at && (
            <InfoRow
              label="Resolved"
              value={new Date(alert.resolved_at).toLocaleString()}
            />
          )}
          {alert.device && (
            <InfoRow label="Device" value={alert.device.name || 'Unknown Device'} />
          )}
        </View>
      </View>

      {alert.context && Object.keys(alert.context).length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Context</Text>
          <View style={styles.infoCard}>
            {Object.entries(alert.context).map(([key, value]) => (
              <InfoRow
                key={key}
                label={key}
                value={typeof value === 'object' ? JSON.stringify(value) : String(value)}
              />
            ))}
          </View>
        </View>
      )}

      {!alert.resolved && (
        <View style={styles.section}>
          <TouchableOpacity
            style={[styles.resolveButton, resolving && styles.buttonDisabled]}
            onPress={handleResolve}
            disabled={resolving}
          >
            {resolving ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={20} color="#ffffff" />
                <Text style={styles.resolveButtonText}>Mark as Resolved</Text>
              </>
            )}
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleString();
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
  severityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 16,
    gap: 8,
  },
  severityText: {
    fontSize: 16,
    fontWeight: '600',
  },
  alertMessage: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text,
    textAlign: 'center',
    marginBottom: 8,
  },
  alertType: {
    fontSize: 14,
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
    flex: 1,
    textAlign: 'right',
  },
  resolveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.ok,
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  resolveButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
