import type { Order, OrderCategory } from '../../types/models';
import { ApiError, deliverClone } from './client';
import { baseOrders } from './seed';

let queuedFailures = 0;
let listOrdersCallCount = 0;

export async function listOrders(category?: OrderCategory | 'All'): Promise<Order[]> {
  listOrdersCallCount += 1;

  if (queuedFailures > 0) {
    queuedFailures -= 1;
    throw new ApiError('Orders temporarily unavailable.');
  }

  const orders = category && category !== 'All'
    ? baseOrders.filter((order) => order.category === category)
    : baseOrders;
  return deliverClone(orders);
}

export const ordersApiTestControls = {
  queueFailure(count = 1): void {
    queuedFailures = count;
  },
  getCallCount(): number {
    return listOrdersCallCount;
  },
  reset(): void {
    queuedFailures = 0;
    listOrdersCallCount = 0;
  },
};
