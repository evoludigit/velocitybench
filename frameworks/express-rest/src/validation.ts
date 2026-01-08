import Joi from 'joi';

// User validation schemas
export const updateUserSchema = Joi.object({
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
export const createPostSchema = Joi.object({
  title: Joi.string()
    .min(1)
    .max(500)
    .required()
    .messages({
      'string.min': 'Title is required',
      'string.max': 'Title must be at most 500 characters',
      'string.base': 'Title must be a string',
      'any.required': 'Title is required'
    }),

  content: Joi.string()
    .max(10000)
    .optional()
    .messages({
      'string.max': 'Content must be at most 10000 characters',
      'string.base': 'Content must be a string'
    })
}).messages({
  'object.unknown': 'Unknown field: #{#key}'
});