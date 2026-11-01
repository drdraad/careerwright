import { forwardToApi } from "@/lib/apiProxy";
import { webConfig } from "@/lib/config";

export const dynamic = "force-dynamic";

type Context = { params: Promise<{ path: string[] }> };

async function forward(request: Request, { params }: Context): Promise<Response> {
  const { path } = await params;
  return forwardToApi(request, path, webConfig().apiInternalUrl);
}

export { forward as DELETE, forward as GET, forward as PATCH, forward as POST, forward as PUT };
