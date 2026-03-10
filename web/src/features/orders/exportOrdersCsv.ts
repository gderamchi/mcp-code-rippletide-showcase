import type { Order } from '../../types/models';

export function exportOrdersCsv(orders: Order[]): string {
  const rows = orders.map((order) =>
    [
      order.id,
      order.customerName,
      order.category,
      order.status,
      order.owner,
      order.total.toFixed(2),
    ].join(',')
  );

  return ['Order ID,Customer,Category,Status,Owner,Total', ...rows].join('\n');
}
