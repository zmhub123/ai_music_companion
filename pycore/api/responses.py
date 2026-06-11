"""
标准化的 API 响应模型。

在所有端点间提供一致的响应格式。
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    标准 API 响应包装器。

    用法：
        # 成功响应
        return APIResponse(
            code=200,
            message="success",
            data={"user_id": 123}
        )

        # 错误响应
        return APIResponse(
            code=404,
            message="User not found",
            data=None
        )
    """

    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    request_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaginationMeta(BaseModel):
    """分页元数据。"""

    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class PaginationData(BaseModel, Generic[T]):
    """分页数据载荷。"""

    items: list[T] = Field(default_factory=list)
    pagination: PaginationMeta


class PaginatedResponse(APIResponse[PaginationData[T]], Generic[T]):
    """
    分页 API 响应。

    用法：
        return PaginatedResponse(
            data=PaginationData(items=items, pagination=pagination)
        )
    """


def success_response(
    data: Any = None,
    message: str = "success",
    code: int = 200,
    request_id: Optional[str] = None,
    **metadata,
) -> APIResponse:
    """
    创建成功响应。

    用法：
        return success_response({"user": user_data})
        return success_response(user, message="User created")
    """
    return APIResponse(
        code=code,
        message=message,
        data=data,
        request_id=request_id,
        metadata=metadata,
    )


def error_response(
    error: str,
    error_code: Optional[str] = None,
    status_code: int = 400,
    request_id: Optional[str] = None,
    **metadata,
) -> tuple[APIResponse, int]:
    """
    创建带状态码的错误响应。

    用法：
        return error_response("User not found", "USER_NOT_FOUND", 404)
    """
    if error_code:
        metadata = {**metadata, "error_code": error_code}
    response = APIResponse(
        code=status_code,
        message=error,
        data=None,
        request_id=request_id,
        metadata=metadata,
    )
    return response, status_code


def paginated_response(
    data: list[Any],
    page: int = 1,
    page_size: int = 20,
    total_items: int = 0,
    request_id: Optional[str] = None,
) -> PaginatedResponse:
    """
    创建分页响应。

    用法：
        items = get_items(page=1, limit=20)
        total = count_items()
        return paginated_response(items, page=1, page_size=20, total_items=total)
    """
    total_pages = (total_items + page_size - 1) // page_size if page_size > 0 else 0

    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

    return PaginatedResponse(
        code=200,
        message="success",
        data=PaginationData(items=data, pagination=pagination),
        request_id=request_id,
    )
