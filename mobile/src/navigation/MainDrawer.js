import React from 'react';
import { createDrawerNavigator } from '@react-navigation/drawer';
import CustomDrawerContent from './CustomDrawerContent';
import { colors } from '../theme';

// Screens
import DashboardScreen from '../screens/DashboardScreen';
import DevicesScreen from '../screens/DevicesScreen';
import AlertsScreen from '../screens/AlertsScreen';
import FamilyScreen from '../screens/FamilyScreen';
import SettingsScreen from '../screens/SettingsScreen';
import AuditLogsScreen from '../screens/AuditLogsScreen';
import IncidentsScreen from '../screens/IncidentsScreen';
import SecurityThreatsScreen from '../screens/SecurityThreatsScreen';
import SecurityComplianceScreen from '../screens/SecurityComplianceScreen';
import PricingScreen from '../screens/PricingScreen';

const Drawer = createDrawerNavigator();

const screenOptions = {
  headerStyle: { backgroundColor: colors.surface },
  headerTintColor: colors.text,
  headerTitleStyle: { fontWeight: '600', fontSize: 18 },
  drawerType: 'front',
  drawerStyle: { backgroundColor: colors.surface, width: 280 },
  drawerActiveTintColor: colors.primary,
  drawerInactiveTintColor: colors.muted,
  sceneContainerStyle: { backgroundColor: colors.bg },
};

export default function MainDrawer() {
  return (
    <Drawer.Navigator
      drawerContent={(props) => <CustomDrawerContent {...props} />}
      screenOptions={screenOptions}
    >
      <Drawer.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Dashboard' }} />
      <Drawer.Screen name="Devices" component={DevicesScreen} options={{ title: 'Devices' }} />
      <Drawer.Screen name="Alerts" component={AlertsScreen} options={{ title: 'Alerts' }} />
      <Drawer.Screen name="Family" component={FamilyScreen} options={{ title: 'Family' }} />
      <Drawer.Screen name="Settings" component={SettingsScreen} options={{ title: 'Settings' }} />
      <Drawer.Screen name="AuditLogs" component={AuditLogsScreen} options={{ title: 'Audit Logs' }} />
      <Drawer.Screen name="Incidents" component={IncidentsScreen} options={{ title: 'Incidents' }} />
      <Drawer.Screen name="SecurityThreats" component={SecurityThreatsScreen} options={{ title: 'Security Threats' }} />
      <Drawer.Screen name="SecurityCompliance" component={SecurityComplianceScreen} options={{ title: 'Security & Compliance' }} />
      <Drawer.Screen name="Pricing" component={PricingScreen} options={{ title: 'Pricing' }} />
    </Drawer.Navigator>
  );
}
