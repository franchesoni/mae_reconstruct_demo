import os
from types import MethodType
from PIL import Image
import numpy as np
import time

from mae_visualize_modified import imagenet_normalize, masking_from_mask, patchify_mask, prepare_model, prepare_model_dummy, run_one_image

# if you need to access a file next to the source code, use the variable ROOT
# for example:
#    torch.load(os.path.join(ROOT, 'weights.pth'))
ROOT = os.path.dirname(os.path.realpath(__file__))

def minmaxnorm(x):
    return (x - x.min()) / (x.max() - x.min())

def main(input, loss, output):
    img = np.array(Image.open(input).resize((224, 224))) / 255.
    assert img.shape == (224, 224, 3)
    mask = (np.array(Image.open("mask_0.png").resize((224, 224), Image.NEAREST))[..., -1] > 0).astype(bool)[..., None]
    assert mask.shape == (224, 224, 1)
    img = imagenet_normalize(img)

    st = time.time()
    if loss == "MSE" and os.path.exists("mae_visualize_vit_large.pth"):
        chkpt_dir = 'mae_visualize_vit_large.pth'
        model_mae = prepare_model(chkpt_dir, 'mae_vit_large_patch16')
    elif loss == "GAN" and os.path.exists("mae_visualize_vit_large_ganloss.pth"):
        chkpt_dir = 'mae_visualize_vit_large_ganloss.pth'
        model_mae = prepare_model('mae_visualize_vit_large_ganloss.pth', 'mae_vit_large_patch16')
    else:
        print("No model found for loss type " + loss)
        print(f"Directory contains: {os.listdir()}")
        print("Loading model with random weights")
        model_mae = prepare_model_dummy('mae_vit_large_patch16')

    model_mae.patchify_mask = MethodType(patchify_mask, model_mae) 
    model_mae.random_masking = MethodType(masking_from_mask, model_mae)
    print(f'Model loaded in {time.time()-st}s.')
    original, masked, reconstruction, reconstructionplusvisible = run_one_image(img, mask, model_mae)

    Image.fromarray(original).save("original.png")
    Image.fromarray(masked).save("masked.png")
    Image.fromarray(reconstruction).save("reconstruction.png")
    Image.fromarray(reconstructionplusvisible).save("reconstructionplusvisible.png")
    Image.fromarray(reconstructionplusvisible).save(output)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--loss", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)

    args = parser.parse_args()
    main(args.input, args.loss, args.output)
