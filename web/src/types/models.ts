export type OrderCategory = 'Hardware' | 'Software' | 'Services';
export type OrderStatus = 'Ready' | 'Delayed' | 'At Risk';
export type CustomerSegment = 'Strategic' | 'Growth' | 'Pilot' | 'Dormant';
export type ThemePreference = 'system' | 'light' | 'dark';

export interface Order {
  id: string;
  customerName: string;
  category: OrderCategory;
  status: OrderStatus;
  total: number;
  owner: string;
}

export interface Customer {
  id: string;
  name: string;
  segment: CustomerSegment;
  owner: string;
  lastOrderDate: string;
}

export interface AppSettings {
  lowStockAlerts: boolean;
  theme: ThemePreference;
}
