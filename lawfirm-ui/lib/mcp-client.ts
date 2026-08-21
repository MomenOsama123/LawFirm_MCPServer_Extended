type ToolResponse<T> = {
  tool: string
  data: T
}

const adminApiUrl = process.env.NEXT_PUBLIC_ADMIN_API_URL ?? "http://127.0.0.1:8001"

export async function callMcpTool<T>(tool: string, arguments_: Record<string, string | number>) {
  const response = await fetch(`${adminApiUrl}/admin/tools/mcp/call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tool, arguments: arguments_ }),
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `MCP tool ${tool} failed`)
  }

  return (await response.json()) as ToolResponse<T>
}