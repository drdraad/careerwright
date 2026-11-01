import {
  AdditiveBlending,
  BufferAttribute,
  BufferGeometry,
  Camera,
  DoubleSide,
  GLSL3,
  InstancedBufferAttribute,
  InstancedBufferGeometry,
  Mesh,
  NoBlending,
  Points,
  RawShaderMaterial,
  Scene,
  WebGLRenderer,
} from "three";
import { type Adapter, COUNTS, SHADERS, type Setup } from "./scene.ts";

export async function create({ canvas, w, h, dpr, buffers }: Setup): Promise<Adapter> {
  const renderer = new WebGLRenderer({ canvas, antialias: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(dpr);
  renderer.setSize(w, h, false);
  renderer.setClearColor(0x03050a, 1);
  const uniforms = { uTime: { value: 0 }, uRes: { value: [w, h] }, uDpr: { value: canvas.width / w } };
  const material = (s: { vertex: string; fragment: string }, additive: boolean) =>
    new RawShaderMaterial({
      glslVersion: GLSL3,
      uniforms,
      vertexShader: s.vertex,
      fragmentShader: s.fragment,
      blending: additive ? AdditiveBlending : NoBlending,
      transparent: additive,
      side: DoubleSide,
      depthTest: false,
      depthWrite: false,
    });
  const scene = new Scene();
  const add = (object: Mesh | Points, order: number) => {
    object.frustumCulled = false;
    object.renderOrder = order;
    scene.add(object);
  };

  const backdrop = new BufferGeometry();
  backdrop.setAttribute("position", new BufferAttribute(buffers.backdrop, 3));
  add(new Mesh(backdrop, material(SHADERS.background, false)), 0);

  const trails = new BufferGeometry();
  trails.setAttribute("position", new BufferAttribute(buffers.trail.position, 3));
  trails.setAttribute("aData", new BufferAttribute(buffers.trail.data, 4));
  trails.setIndex(new BufferAttribute(buffers.trail.index, 1));
  add(new Mesh(trails, material(SHADERS.trail, true)), 1);

  const dust = new BufferGeometry();
  dust.setAttribute("position", new BufferAttribute(buffers.particles.position, 3));
  dust.setAttribute("aSeed", new BufferAttribute(buffers.particles.seed, 4));
  add(new Points(dust, material(SHADERS.particle, true)), 2);

  const lights = new InstancedBufferGeometry();
  lights.setAttribute("position", new BufferAttribute(buffers.quad.position, 3));
  lights.setIndex(new BufferAttribute(buffers.quad.index, 1));
  lights.setAttribute("iP", new InstancedBufferAttribute(buffers.lights.p, 3));
  lights.setAttribute("iA", new InstancedBufferAttribute(buffers.lights.a, 4));
  lights.instanceCount = COUNTS.lights;
  add(new Mesh(lights, material(SHADERS.light, true)), 3);

  const camera = new Camera();
  return {
    gl: renderer.getContext() as WebGL2RenderingContext,
    render(seconds) {
      uniforms.uTime.value = seconds;
      renderer.render(scene, camera);
    },
  };
}
