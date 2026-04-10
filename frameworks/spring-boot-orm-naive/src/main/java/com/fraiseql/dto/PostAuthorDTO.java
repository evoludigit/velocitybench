package com.fraiseql.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PostAuthorDTO {
    private String id;
    private String username;
    private String fullName;
}
