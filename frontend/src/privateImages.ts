import { ApiError, getBlob } from "./api";

// 私密图片加载：优先使用后端的有界预览图（更省流量、加载更快），
// 后端没有预览路由时回退到原图下载。返回 Blob，对象 URL 由调用方管理。
export async function loadPrivateImage(
  path: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const file = /^\/files\/([^/?#]+)/.exec(path);
  if (file) {
    try {
      return await getBlob(`/files/${file[1]}/preview`, signal);
    } catch (error) {
      // 仅当预览路由不存在（404）时回退原图；其他错误照实抛出。
      if (!(error instanceof ApiError) || error.status !== 404) throw error;
    }
  }
  return getBlob(path, signal);
}
