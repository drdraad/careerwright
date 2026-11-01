// PixiJS generates code with eval unless this module replaces it; the spike's (and the product's)
// content security policy forbids eval.
import "pixi.js/unsafe-eval";
import { Application, Geometry, Mesh, Shader, UniformGroup } from "pixi.js";
import { type Adapter, COUNTS, SHADERS, type Setup } from "./scene.ts";

export async function create({ canvas, w, h, dpr, buffers }: Setup): Promise<Adapter> {
  const app = new Application();
  await app.init({
    canvas,
    width: w,
    height: h,
    resolution: dpr,
    autoDensity: false,
    antialias: false,
    background: "#03050a",
    preference: "webgl",
    autoStart: false,
    sharedTicker: false,
    powerPreference: "high-performance",
  });
  const uniforms = new UniformGroup({
    uTime: { value: 0, type: "f32" },
    uRes: { value: new Float32Array([w, h]), type: "vec2<f32>" },
    uDpr: { value: canvas.width / w, type: "f32" },
  });
  // PixiJS treats a shader without a #version line as WebGL1 GLSL, so the line is added here.
  const shader = (s: { vertex: string; fragment: string }) =>
    Shader.from({
      gl: { vertex: `#version 300 es\n${s.vertex}`, fragment: `#version 300 es\n${s.fragment}` },
      resources: { benchUniforms: uniforms },
    });
  const add = (geometry: Geometry, s: { vertex: string; fragment: string }, additive: boolean) => {
    const mesh = new Mesh({ geometry, shader: shader(s) });
    if (additive) mesh.blendMode = "add";
    mesh.state.culling = false;
    app.stage.addChild(mesh);
  };

  add(new Geometry({ attributes: { position: { buffer: buffers.backdrop, format: "float32x3" } } }), SHADERS.background, false);
  add(
    new Geometry({
      attributes: {
        position: { buffer: buffers.trail.position, format: "float32x3" },
        aData: { buffer: buffers.trail.data, format: "float32x4" },
      },
      indexBuffer: buffers.trail.index,
    }),
    SHADERS.trail,
    true,
  );
  add(
    new Geometry({
      topology: "point-list",
      attributes: {
        position: { buffer: buffers.particles.position, format: "float32x3" },
        aSeed: { buffer: buffers.particles.seed, format: "float32x4" },
      },
    }),
    SHADERS.particle,
    true,
  );
  add(
    new Geometry({
      attributes: {
        position: { buffer: buffers.quad.position, format: "float32x3" },
        iP: { buffer: buffers.lights.p, format: "float32x3", instance: true },
        iA: { buffer: buffers.lights.a, format: "float32x4", instance: true },
      },
      indexBuffer: buffers.quad.index,
      instanceCount: COUNTS.lights,
    }),
    SHADERS.light,
    true,
  );

  const renderer = app.renderer as unknown as { gl: WebGL2RenderingContext };
  return {
    gl: renderer.gl,
    render(seconds) {
      uniforms.uniforms.uTime = seconds;
      app.renderer.render(app.stage);
    },
  };
}
