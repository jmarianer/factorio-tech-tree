import { useParams } from "react-router-dom";
import { useData } from "./DataContext";
import { BBCode } from "./BBCode";
import { Dialog } from "./Dialog";
import { CraftingMachine as CraftingMachineType } from "./FactorioTypes";
import { RenderRecipe } from "./Elements";

function CraftingMachine({ entity }: { entity: CraftingMachineType }) {
  const data = useData();
  return <>
    <h2>Crafting</h2>
    {entity.crafting_categories.map((category) => (
      <div key={category}>
        <h3>{category}</h3>
        <div className="recipe-list">
          {Object.values(data.recipes).filter((recipe) => recipe.crafting_category === category).map((recipe) => (
            <RenderRecipe key={recipe.name} recipe={recipe} />
          ))}
        </div>
      </div>
    ))}
  </>;
} 

export default function Entity() {
  const { regime, name } = useParams();
  const data = useData();
  const entity = data.entities[name!];
  return Dialog(`Entity: ${entity.name}`,
    <>
      <img src={`/generated/${regime}/icons/${entity.type}/${entity.name}.png`} alt={entity.name} />
      <div className="description">
        <BBCode code={entity.description('en')} />
      </div>
    </>,
    entity instanceof CraftingMachineType ? <CraftingMachine entity={entity} /> : <> </>
  );
}