from .cmyk_magic import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

# Serve the preset library to the web panel; harmless to skip headless.
try:
    from aiohttp import web
    from server import PromptServer

    from .cmyk_magic import resolve_settings, run_resolved
    from .help_text import HELP
    from .magic_presets import MAGIC_PRESETS, PALETTES, PRESET_DESC
    from .preview import render_png, render_thumb

    @PromptServer.instance.routes.get("/cmyk_magic/presets")
    async def _cmyk_magic_presets(request):
        return web.json_response({"presets": MAGIC_PRESETS, "palettes": PALETTES,
                                  "help": HELP, "preset_desc": PRESET_DESC})

    @PromptServer.instance.routes.get("/cmyk_magic/preset_thumb")
    async def _cmyk_magic_preset_thumb(request):
        """One cached engine render per preset, for the gallery."""
        name = request.query.get("name", "")
        try:
            png = render_thumb(name, MAGIC_PRESETS, resolve_settings, run_resolved)
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)
        if png is None:
            return web.json_response({"error": "unknown preset"}, status=404)
        return web.Response(body=png, content_type="image/png",
                            headers={"Cache-Control": "max-age=86400"})

    @PromptServer.instance.routes.post("/cmyk_magic/preview")
    async def _cmyk_magic_preview(request):
        """Render the panel's live preview with the real engine."""
        try:
            params = await request.json()
            png, is_own, preset = render_png(params.get("node_id"), params,
                                             resolve_settings, run_resolved)
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)
        return web.Response(body=png, content_type="image/png",
                            headers={"X-Preview-Source": "input" if is_own else "testcard",
                                     "X-Preset": preset or "Custom"})
except Exception:
    pass
