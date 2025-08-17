import functools
import inspect
from typing import (Any, Callable, Dict, List, Optional, Sequence, Type,
                    TypeVar, Union)

# Export symbols to abstract fastapi in implementors code
from fastapi import APIRouter, BackgroundTasks, Body, Cookie, Depends
from fastapi import FastAPI as RootRouter
from fastapi import Request, Response, status
from fastapi.datastructures import Default, DefaultPlaceholder
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute, BaseRoute
from fastapi.testclient import TestClient

from gmail_helper.common.utils.exceptions import Reason, ServiceException
from gmail_helper.common.utils.logger import get_logger

LOG = get_logger(__name__)
T = TypeVar("T")
IncEx = Union[set, dict]


def api_router(
    prefix: str = "",
    tags: Optional[List[str]] = None,
    dependencies: Optional[Sequence[Depends]] = None,
    default_response_class: Type[Response] = Default(JSONResponse),
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    redirect_slashes: bool = True,
    route_class: Type[APIRoute] = APIRoute,
    on_startup: Optional[Sequence[Callable[[], Any]]] = None,
    on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
    deprecated: Optional[bool] = None,
    include_in_schema: bool = True,
):
    return api_router_(
        prefix=prefix,
        tags=tags,
        dependencies=dependencies,
        default_response_class=default_response_class,
        responses=responses,
        redirect_slashes=redirect_slashes,
        route_class=route_class,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
    )


def api_router_(**kwargs):
    def decorator(func):
        routers = func.__dict__.get("__api_router__", list())
        routers.append(kwargs)
        func.__api_router__ = routers
        return func

    return decorator


def api_route(path: str, **kwargs):
    def decorator(func):
        routes = func.__dict__.get("__api_route__", list())
        kwargs["path"] = path
        if not kwargs.get("operation_id"):
            suffix = f"_{len(routes)+1}" if routes else ""
            kwargs["operation_id"] = func.__qualname__ + suffix
        routes.append(kwargs)
        func.__api_route__ = routes
        return func

    return decorator


def api_get(
    path: str,
    *,
    response_model: Optional[Type[Any]] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    dependencies: Optional[Sequence[Depends]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_description: str = "Successful Response",
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    deprecated: Optional[bool] = None,
    operation_id: Optional[str] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    name: Optional[str] = None,
    route_class_override: Optional[Type[APIRoute]] = None,
    callbacks: Optional[List[BaseRoute]] = None,
):
    return api_route(
        path,
        methods=["GET"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        dependencies=dependencies,
        summary=summary,
        description=description,
        response_description=response_description,
        responses=responses,
        deprecated=deprecated,
        operation_id=operation_id,
        response_model_include=response_model_include,
        response_model_exclude=response_model_exclude,
        response_model_by_alias=response_model_by_alias,
        response_model_exclude_unset=response_model_exclude_unset,
        response_model_exclude_defaults=response_model_exclude_defaults,
        response_model_exclude_none=response_model_exclude_none,
        include_in_schema=include_in_schema,
        response_class=response_class,
        name=name,
        route_class_override=route_class_override,
        callbacks=callbacks,
    )


def api_post(
    path: str,
    *,
    response_model: Optional[Type[Any]] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    dependencies: Optional[Sequence[Depends]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_description: str = "Successful Response",
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    deprecated: Optional[bool] = None,
    operation_id: Optional[str] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    name: Optional[str] = None,
    route_class_override: Optional[Type[APIRoute]] = None,
    callbacks: Optional[List[BaseRoute]] = None,
):
    return api_route(
        path,
        methods=["POST"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        dependencies=dependencies,
        summary=summary,
        description=description,
        response_description=response_description,
        responses=responses,
        deprecated=deprecated,
        operation_id=operation_id,
        response_model_include=response_model_include,
        response_model_exclude=response_model_exclude,
        response_model_by_alias=response_model_by_alias,
        response_model_exclude_unset=response_model_exclude_unset,
        response_model_exclude_defaults=response_model_exclude_defaults,
        response_model_exclude_none=response_model_exclude_none,
        include_in_schema=include_in_schema,
        response_class=response_class,
        name=name,
        route_class_override=route_class_override,
        callbacks=callbacks,
    )


def api_delete(
    path: str,
    *,
    response_model: Optional[Type[Any]] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    dependencies: Optional[Sequence[Depends]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_description: str = "Successful Response",
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    deprecated: Optional[bool] = None,
    operation_id: Optional[str] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    name: Optional[str] = None,
    route_class_override: Optional[Type[APIRoute]] = None,
    callbacks: Optional[List[BaseRoute]] = None,
):
    return api_route(
        path,
        methods=["DELETE"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        dependencies=dependencies,
        summary=summary,
        description=description,
        response_description=response_description,
        responses=responses,
        deprecated=deprecated,
        operation_id=operation_id,
        response_model_include=response_model_include,
        response_model_exclude=response_model_exclude,
        response_model_by_alias=response_model_by_alias,
        response_model_exclude_unset=response_model_exclude_unset,
        response_model_exclude_defaults=response_model_exclude_defaults,
        response_model_exclude_none=response_model_exclude_none,
        include_in_schema=include_in_schema,
        response_class=response_class,
        name=name,
        route_class_override=route_class_override,
        callbacks=callbacks,
    )


def api_put(
    path: str,
    *,
    response_model: Optional[Type[Any]] = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
    dependencies: Optional[Sequence[Depends]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_description: str = "Successful Response",
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    deprecated: Optional[bool] = None,
    operation_id: Optional[str] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: Union[Type[Response], DefaultPlaceholder] = Default(JSONResponse),
    name: Optional[str] = None,
    route_class_override: Optional[Type[APIRoute]] = None,
    callbacks: Optional[List[BaseRoute]] = None,
):
    return api_route(
        path,
        methods=["PUT"],
        response_model=response_model,
        status_code=status_code,
        tags=tags,
        dependencies=dependencies,
        summary=summary,
        description=description,
        response_description=response_description,
        responses=responses,
        deprecated=deprecated,
        operation_id=operation_id,
        response_model_include=response_model_include,
        response_model_exclude=response_model_exclude,
        response_model_by_alias=response_model_by_alias,
        response_model_exclude_unset=response_model_exclude_unset,
        response_model_exclude_defaults=response_model_exclude_defaults,
        response_model_exclude_none=response_model_exclude_none,
        include_in_schema=include_in_schema,
        response_class=response_class,
        name=name,
        route_class_override=route_class_override,
        callbacks=callbacks,
    )


TClass = TypeVar("TClass", bound=object)


def routers_from_class(
    cls: Type[TClass], factory: Callable[[], TClass]
) -> List[APIRouter]:
    routers = cls.__dict__.get("__api_router__", [{}])
    result = list()
    for params in routers:
        params = params.copy()
        router = APIRouter(**params)
        add_routes_from_class(router, cls, factory)
        result.append(router)
    return result


def add_routes_from_class(
    api: Union[APIRouter, RootRouter],
    cls: Type[TClass],
    factory: Callable[[], TClass] = None,
):
    if factory is None:
        factory = cls

    for name, func in cls.__dict__.items():
        if not callable(func) or "__api_route__" not in func.__dict__:
            continue

        wrapper = _create_wrapper(func, factory)
        routes = func.__dict__["__api_route__"]
        for route in routes:
            route = route.copy()
            path = route.pop("path")

            if isinstance(api, RootRouter):
                check_compatibility(route, "callbacks")
                check_compatibility(route, "route_class_override")

            LOG.info(f"Installing route for {path}: {func.__qualname__}")
            api.add_api_route(path, wrapper, **route)


def check_compatibility(route: dict, attribute_name: str):
    if route.get(attribute_name):
        raise ValueError(
            f"Can not use {attribute_name} with root router, use a child router instead"
        )
    elif attribute_name in route:
        route.pop(attribute_name)


def _create_wrapper(func, self_factory):
    def wrapper(*args, **kwargs):
        return getattr(self_factory(), func.__name__)(*args, **kwargs)

    functools.update_wrapper(wrapper, func)
    signature = inspect.signature(func)
    new_parameters = list(signature.parameters.values())[1:]
    new_signature = inspect.Signature(
        new_parameters, return_annotation=signature.return_annotation
    )
    wrapper.__signature__ = new_signature
    return wrapper


def add_routers(
    router: RootRouter,
    routers: List[APIRouter],
    deprecated: bool = None,
    dependencies: List[Depends] = None,
    prefix: str = "",
):
    for r in routers:
        router.include_router(
            r, deprecated=deprecated, dependencies=dependencies, prefix=prefix
        )
    router.add_exception_handler(ServiceException, exception_handler)
    return router


def exception_handler(request: Request, exc: ServiceException):
    LOG.critical(
        f"{request.method} {request.url} ({request.query_params}): {exc}", exc_info=True
    )
    mapping = {
        Reason.BAD_REQUEST.name: status.HTTP_400_BAD_REQUEST,
        Reason.ENTITY_NOT_FOUND.name: status.HTTP_404_NOT_FOUND,
        Reason.MISSING_PARAMS.name: status.HTTP_400_BAD_REQUEST,
        Reason.UNAUTHORIZED.name: status.HTTP_403_FORBIDDEN,
        Reason.EXECUTION_ERROR.name: status.HTTP_500_INTERNAL_SERVER_ERROR,
        Reason.INVALID_PARAM.name: status.HTTP_400_BAD_REQUEST,
        Reason.NOT_PROCESSED.name: status.HTTP_400_BAD_REQUEST,
        Reason.MISSING_DATA.name: status.HTTP_400_BAD_REQUEST,
        Reason.INVALID_DATA.name: status.HTTP_400_BAD_REQUEST,
        Reason.CONFLICT.name: status.HTTP_409_CONFLICT,
    }
    status_code = mapping.get(
        exc.get_code().name, status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    return JSONResponse(
        status_code=status_code, content={"message": str(exc.get_message())}
    )
