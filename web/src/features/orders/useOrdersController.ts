import { useEffect, useState } from 'react';
import type { Order, OrderCategory } from '../../types/models';
import { listOrders } from '../../lib/api/orders';
import { exportOrdersCsv } from './exportOrdersCsv';

export interface OrdersControllerState {
  status: 'loading' | 'ready' | 'error';
  selectedCategory: OrderCategory | 'All';
  orders: Order[];
  errorMessage: string | null;
  exportedCsv: string | null;
}

export function useOrdersController(): {
  state: OrdersControllerState;
  setSelectedCategory: (value: OrderCategory | 'All') => void;
  retry: () => Promise<void>;
  exportCurrent: () => void;
} {
  const [state, setState] = useState<OrdersControllerState>({
    status: 'loading',
    selectedCategory: 'All',
    orders: [],
    errorMessage: null,
    exportedCsv: null,
  });

  async function loadOrders(category: OrderCategory | 'All'): Promise<void> {
    setState((current) => ({
      ...current,
      status: 'loading',
      errorMessage: null,
    }));

    try {
      const orders = await listOrders(category);
      setState((current) => ({
        ...current,
        status: 'ready',
        orders,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        status: 'error',
        errorMessage: error instanceof Error ? error.message : 'Unexpected orders failure.',
      }));
    }
  }

  useEffect(() => {
    void loadOrders(state.selectedCategory);
  }, [state.selectedCategory]);

  return {
    state,
    setSelectedCategory(value) {
      setState((current) => ({
        ...current,
        selectedCategory: value,
      }));
    },
    async retry() {
      await loadOrders(state.selectedCategory);
    },
    exportCurrent() {
      setState((current) => ({
        ...current,
        exportedCsv: exportOrdersCsv(current.orders),
      }));
    },
  };
}
