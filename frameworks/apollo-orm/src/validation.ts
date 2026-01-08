import Joi from 'joi';

// User validation schemas
export const updateUserSchema = Joi.object({
  id: Joi.string().uuid().required(),
  fullName: Joi.string()
    .max(255)
    .optional()
    .messages({
      'string.max': 'Full name must be at most 255 characters',
      'string.base': 'Full name must be a string'
    }),

  bio: Joi.string()
    .max(1000)
    .optional()
    .messages({
      'string.max': 'Bio must be at most 1000 characters',
      'string.base': 'Bio must be a string'
    })
}).messages({
  'object.unknown': 'Unknown field: #{#key}'
});