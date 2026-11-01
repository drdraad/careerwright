import { Geometry, Mesh, Program, Renderer, Transform } from "ogl";
import { type Adapter, COUNTS, SHADERS, type Setup } from "./scene.ts";

export async function create({ canvas, w, h, dpr, buffers }: Setup): Promise<Adapter> {
  const renderer = new Renderer({ canvas, width: w, height: h, dpr, webgl: 2, antialias: false, powerPreference: "high-performance" });
  const gl = renderer.gl;
  gl.clearColor(0.012, 0.02, 0.04, 1);
  const uniforms = { uTime: { value: 0 }, uRes: { value: [w, h] }, uDpr: { value: canvas.width / w } };
  const program = (s: { vertex: string; fragment: string }, additive: boolean) => {
    const p = new Program(gl, {
      vertex: `#version 300 es\n${s.vertex}`,
      fragment: `#version 300 es\n${s.fragment}`,
      uniforms,
      transparent: additive,
      cullFace: false,
      depthTest: false,
      depthWrite: false,
    });
    if (additive) p.setBlendFunc(gl.ONE, gl.ONE);
    return p;
  };
  const scene = new Transform();

  new Mesh(gl, {
    geometry: new Geometry(gl, { position: { size: 3, data: buffers.backdrop } }),
    program: program(SHADERS.background, false),
  }).setParent(scene);

  new Mesh(gl, {
    geometry: new Geometry(gl, {
      position: { size: 3, data: buffers.trail.position },
      aData: { size: 4, data: buffers.trail.data },
      index: { data: buffers.trail.index },
    }),
    program: program(SHADERS.trail, true),
  }).setParent(scene);

  new Mesh(gl, {
    mode: gl.POINTS,
    geometry: new Geometry(gl, {
      position: { size: 3, data: buffers.particles.position },
      aSeed: { size: 4, data: buffers.particles.seed },
    }),
    program: program(SHADERS.particle, true),
  }).setParent(scene);

  const lights = new Geometry(gl, {
    position: { size: 3, data: buffers.quad.position },
    index: { data: buffers.quad.index },
    iP: { instanced: 1, size: 3, data: buffers.lights.p },
    iA: { instanced: 1, size: 4, data: buffers.lights.a },
  });
  lights.instancedCount = COUNTS.lights;
  new Mesh(gl, { geometry: lights, program: program(SHADERS.light, true) }).setParent(scene);

  return {
    gl: gl as unknown as WebGL2RenderingContext,
    render(seconds) {
      uniforms.uTime.value = seconds;
      renderer.render({ scene, sort: false, frustumCull: false });
    },
  };
}
