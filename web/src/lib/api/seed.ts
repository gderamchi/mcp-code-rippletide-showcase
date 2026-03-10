import type { AppSettings, Customer, Order } from '../../types/models';

export const baseOrders: Order[] = [
  {
    id: 'ord-101',
    customerName: 'Northwind Capital',
    category: 'Hardware',
    status: 'Ready',
    total: 12450,
    owner: 'Mina',
  },
  {
    id: 'ord-102',
    customerName: 'Canvas Grid',
    category: 'Software',
    status: 'Delayed',
    total: 8640,
    owner: 'Julian',
  },
  {
    id: 'ord-103',
    customerName: 'Harbor Relay',
    category: 'Services',
    status: 'At Risk',
    total: 5160,
    owner: 'Sora',
  },
];

export const baseCustomers: Customer[] = [
  {
    id: 'cus-1',
    name: 'Northwind Capital',
    segment: 'Strategic',
    owner: 'Mina',
    lastOrderDate: '2026-03-08',
  },
  {
    id: 'cus-2',
    name: 'Canvas Grid',
    segment: 'Growth',
    owner: 'Julian',
    lastOrderDate: '2026-03-05',
  },
  {
    id: 'cus-3',
    name: 'Harbor Relay',
    segment: 'Pilot',
    owner: 'Sora',
    lastOrderDate: '2026-02-27',
  },
];

export const defaultSettings: AppSettings = {
  lowStockAlerts: true,
  theme: 'system',
};
