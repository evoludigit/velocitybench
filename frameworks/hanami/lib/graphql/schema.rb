# frozen_string_literal: true

module VelocityBench
  module GraphQL
    class Schema < ::GraphQL::Schema
      query Types::QueryType
      mutation Types::MutationType

      # Use GraphQL::Batch for DataLoader support
      use ::GraphQL::Batch

      # Error handling
      def self.resolve_type(_type, _obj, _ctx)
        raise "Abstract type resolution not implemented"
      end

      def self.id_from_object(object, _type, _ctx)
        object.id.to_s
      end

      def self.object_from_id(id, _ctx)
        # Not implemented for benchmark
        nil
      end
    end
  end
end
