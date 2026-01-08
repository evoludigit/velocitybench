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

// Post validation schemas
export const updatePostSchema = Joi.object({
  id: Joi.string().uuid().required(),
  title: Joi.string()
    .max(500)
    .optional()
    .messages({
      'string.max': 'Title must be at most 500 characters',
      'string.base': 'Title must be a string'
    }),

  content: Joi.string()
    .max(10000)
    .optional()
    .allow(null)
    .messages({
      'string.max': 'Content must be at most 10000 characters',
      'string.base': 'Content must be a string'
    })
}).messages({
  'object.unknown': 'Unknown field: #{#key}'
});