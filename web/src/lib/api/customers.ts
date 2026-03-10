import type { Customer, CustomerSegment } from '../../types/models';
import { deliverClone } from './client';
import { baseCustomers } from './seed';

export async function listCustomers(segment?: CustomerSegment | 'All'): Promise<Customer[]> {
  const customers = segment && segment !== 'All'
    ? baseCustomers.filter((customer) => customer.segment === segment)
    : baseCustomers;
  return deliverClone(customers);
}
