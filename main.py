import os
from types import MethodType
from PIL import Image
import numpy as np
import time

from mae_visualize_modified import (
    imagenet_normalize,
    masking_from_mask,
    patchify_mask,
    prepare_model,
    prepare_model_dummy,
    run_one_image,
)

# if you need to access a file next to the source code, use the variable ROOT
# for example:
#    torch.load(os.path.join(ROOT, 'weights.pth'))
ROOT = os.path.dirname(os.path.realpath(__file__))


def minmaxnorm(x):
    return (x - x.min()) / (x.max() - x.min())


def reconstruct_mask(input, loss):
    img = Image.open(input).convert("RGB")
    size = img.size
    img = np.array(img.resize((224, 224))) / 255.0
    assert img.shape == (
        224,
        224,
        3,
    ), f"Expected image to be (224, 224, 3) instead of {img.shape}"
    mask = (
        np.array(Image.open("mask_0.png").resize((224, 224), Image.NEAREST))[
            ..., -1
        ]
        > 0
    ).astype(bool)[..., None]
    assert mask.shape == (
        224,
        224,
        1,
    ), f"Expected mask to be (224, 224, 1) instead of {mask.shape}"
    img = imagenet_normalize(img)

    st = time.time()
    mse_ckpt = os.path.join(ROOT, "mae_visualize_vit_large.pth")
    gan_ckpt = os.path.join(ROOT, "mae_visualize_vit_large_ganloss.pth")
    if loss == "MSE" and os.path.exists(mse_ckpt):
        model_mae = prepare_model(mse_ckpt, "mae_vit_large_patch16")
    elif loss == "GAN" and os.path.exists(gan_ckpt):
        model_mae = prepare_model(gan_ckpt, "mae_vit_large_patch16")
    else:
        print("No model found for loss type " + loss)
        print(f"Directory contains: {os.listdir(ROOT)}")
        print("Loading model with random weights")
        model_mae = prepare_model_dummy("mae_vit_large_patch16")

    model_mae.patchify_mask = MethodType(patchify_mask, model_mae)
    model_mae.random_masking = MethodType(masking_from_mask, model_mae)
    print(f"Model loaded in {time.time()-st}s.")
    (
        original,
        masked,
        reconstruction,
        reconstructionplusvisible,
    ) = run_one_image(img, mask, model_mae)

    Image.fromarray(original).resize(size).save("original.png")
    Image.fromarray(masked).resize(size).save("masked.png")
    Image.fromarray(reconstruction).resize(size).save("reconstruction.png")
    Image.fromarray(reconstructionplusvisible).resize(size).save(
        "reconstructionplusvisible.png"
    )

    Image.fromarray(original).save("originalrs.png")
    Image.fromarray(masked).save("maskedrs.png")
    Image.fromarray(reconstruction).save("reconstructionrs.png")
    Image.fromarray(reconstructionplusvisible).save(
        "reconstructionplusvisiblers.png"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--loss", type=str, required=True)

    args = parser.parse_args()
    reconstruct_mask(args.input, args.loss)
