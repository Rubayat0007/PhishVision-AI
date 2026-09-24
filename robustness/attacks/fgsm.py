import torch


def fgsm_attack(
    model,
    images,
    labels,
    epsilon,
    loss_fn=None,
):
    """
    Generate adversarial examples using the Fast Gradient Sign Method (FGSM).

    Args:
        model: PyTorch classification model.
        images: Input image tensor, shape [N, C, H, W].
        labels: Ground-truth class labels.
        epsilon: FGSM perturbation magnitude.
        loss_fn: Loss function used to calculate the input gradient.

    Returns:
        Adversarial image tensor with values clamped to [0, 1].
    """
    if loss_fn is None:
        loss_fn = torch.nn.CrossEntropyLoss()

    model.eval()

    original_images = images.detach().clone()
    adversarial_images = original_images.clone().detach()
    adversarial_images.requires_grad = True

    model.zero_grad(set_to_none=True)

    outputs = model(adversarial_images)
    loss = loss_fn(outputs, labels)

    loss.backward()

    gradient_sign = adversarial_images.grad.sign()

    adversarial_images = (
        original_images + epsilon * gradient_sign
    ).detach()

    adversarial_images = torch.clamp(
        adversarial_images,
        min=0.0,
        max=1.0,
    )

    return adversarial_images