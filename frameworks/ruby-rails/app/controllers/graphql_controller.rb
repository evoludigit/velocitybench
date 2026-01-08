class GraphqlController < ApplicationController
  def execute
    result = FraiseqlSchema.execute(
      params[:query],
      variables: params[:variables],
      context: {},
      operation_name: params[:operationName]
    )
    
    render json: result
  end
end
