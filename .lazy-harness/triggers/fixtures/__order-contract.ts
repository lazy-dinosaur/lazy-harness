import { z } from 'zod';

export const orderItemSchema = z.object({
  patientId: z.string(),
  treatmentName: z.string(),
  quantity: z.number().min(1),
  status: z.enum(['pending', 'completed', 'cancelled']),
});

export type OrderItem = z.infer<typeof orderItemSchema>;
