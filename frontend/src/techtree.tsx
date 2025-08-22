import { useParams } from "react-router-dom";
import { useData } from './DataContext';
import { Dialog, DialogHeader } from "./Dialog";
import { Tech } from './FactorioTypes';
import { FactorioData } from './FactorioData';

const LAYER_HEIGHT = 300;
const LAYER_WIDTH = 250;
// NOTE: there are more hard-coded numbers later down. :(

export function TechTree() {
  const { techs } = useData<FactorioData>();
  const { regime } = useParams();

  const nodes: Record<string, {tech: Tech, x: number, y: number}> = {};
  const edges: Array<[string, string]> = [];

  let techsRemaining = new Set(Object.keys(techs));
  let techsDone = new Set<string>();

  let y = 0;
  while (true) {
    // eslint-disable-next-line no-loop-func -- (Known false positives with array functions)
    const nextLayer = Array.from(techsRemaining).filter(tech =>
      // @ts-ignore  (isSubsetOf is new enough that TS has problems with it)
      techs[tech].prerequisites.isSubsetOf(techsDone)
    )
    if (nextLayer.length === 0) {
      break;
    }

    let x = 0;
    for (const tech of Array.from(nextLayer)) {
      nodes[tech] = {
        x: (x + y % 2 / 2) * LAYER_WIDTH,
        y: y * LAYER_HEIGHT,
        tech: techs[tech],
      };
      x++;
      if (x === 6) {
        x = 0;
        y++;
      }
    }
    if (x !== 0) {
      y++;
    }
    // @ts-ignore
    techsDone = techsDone.union(new Set(nextLayer));
    // @ts-ignore
    techsRemaining = techsRemaining.difference(new Set(nextLayer));
  }

  Object.values(techs).forEach((tech) => {
    tech.prerequisites.forEach((prereq) => {
      edges.push([ prereq, tech.name ]);
    });
  });

  const TechNode = ({ tech, x, y }: { tech: Tech; x: number; y: number }) => {
    return (
      <div className="tech" style={{top: y, left: x}}>
        <img width={128} height={128} src={`/generated/${regime}/icons/technology/${tech.name}.png`} alt={tech.name} />
        {tech.localized_title('en')}
      </div>
    );
  };

  return <Dialog title='Tech tree'>
    <DialogHeader>
      All {Object.keys(nodes).length} available technologies
    </DialogHeader>
    <div style={{ position: 'relative', overflow: 'auto', height: y * LAYER_HEIGHT }}>
      <svg style={{ position: 'absolute', overflow: 'visible' }}>
        {edges.map(([from, to]) => {
          const from_x = nodes[from].x + 64;
          const from_y = nodes[from].y + 200;
          const to_x = nodes[to].x + 64;
          const to_y = nodes[to].y;
          let curve1 = '', curve2 = '';
          if (from_x < to_x) {
            curve1 = 'q0 10, 10 10';
            curve2 = 'q10 0, 10 10';
          }
          if (from_x > to_x) {
            curve1 = 'q0 10, -10 10';
            curve2 = 'q-10 0, -10 10';
          }
          return (
            <path d={`M${from_x} ${from_y} v50 ${curve1} H${to_x} ${curve2} V${to_y}`} style={{stroke: '#d2d2d2', fill: 'none'}} key={`${from}-${to}`} />
          );
        })}
      </svg>
      {Object.values(nodes).map(node => <TechNode tech={node.tech} x={node.x} y={node.y} key={node.tech.name} />)}
    </div>
  </Dialog>
}