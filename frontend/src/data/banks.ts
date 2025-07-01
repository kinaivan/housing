import { Bank } from '../types';

export const bankOptions: Bank[] = [
  {
    id: 'bank1',
    title: 'ING Bank',
    description: 'One of the largest Dutch banks with competitive rates',
    interestRates: {
      1990: 9.5,
      2000: 6.8,
      2024: 4.2,
    },
    imageUrl: '/images/ing-bank.jpg',
    loanToValue: 0.9, // 90% LTV
    maxLoanTerm: 30,
  },
  {
    id: 'bank2',
    title: 'ABN AMRO',
    description: 'Traditional bank with flexible mortgage options',
    interestRates: {
      1990: 9.8,
      2000: 7.0,
      2024: 4.4,
    },
    imageUrl: '/images/abn-amro.jpg',
    loanToValue: 0.85, // 85% LTV
    maxLoanTerm: 30,
  },
  {
    id: 'bank3',
    title: 'Rabobank',
    description: 'Cooperative bank known for personal service',
    interestRates: {
      1990: 9.3,
      2000: 6.5,
      2024: 4.0,
    },
    imageUrl: '/images/rabobank.jpg',
    loanToValue: 0.95, // 95% LTV
    maxLoanTerm: 30,
  },
]; 