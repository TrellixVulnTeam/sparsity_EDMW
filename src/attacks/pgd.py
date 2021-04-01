import torch

from src.attacks.registry import register

device = "cuda" if torch.cuda.is_available() else "cpu"


@register
class PGD:
    r"""
    PGD in the paper 'Towards Deep Learning Models Resistant to Adversarial Attacks'
    [https://arxiv.org/abs/1706.06083]

    Distance Measure : Linf

    Arguments:
        model (nn.Module): model to attack.
        eps (float): maximum perturbation. (DEFALUT : 0.3)
        alpha (float): step size. (DEFALUT : 2/255)
        steps (int): number of steps. (DEFALUT : 40)
        random_start (bool): using random initialization of delta. (DEFAULT : False)

    Shape:
        - images: :math:`(N, C, H, W)` where `N = number of batches`, `C = number of channels`,        `H = height` and `W = width`. It must have a range [0, 1].
        - labels: :math:`(N)` where each value :math:`y_i` is :math:`0 \leq y_i \leq` `number of labels`.
        - output: :math:`(N, C, H, W)`.

    Examples::
        >>> attack = torchattacks.PGD(model, eps = 8/255, alpha = 1/255, steps=40, random_start=False)
        >>> adv_images = attack(images, labels)

    """

    def __init__(self, criterion, args):
        # super(PGD, self).__init__("PGD", model)
        # self.model = model
        self.args = args
        self.eps = 0.3
        self.alpha = args.alpha
        self.random_start = args.random_start
        self.steps = args.steps
        self.criterion = criterion

    def forward(self, model, images, labels, eps=None):
        r"""
        Overridden.
        """
        images = images.to(device)
        labels = labels.to(device)
        # labels = self._transform_label(images, labels)

        adv_images = images.clone().detach()
        if eps is None:
            eps = self.eps

        if self.random_start:
            # Starting at a uniformly random point
            adv_images = adv_images + torch.empty_like(adv_images).uniform_(-eps, eps)
            adv_images = torch.clamp(adv_images, min=0, max=1)

        for i in range(self.steps):
            adv_images.requires_grad = True
            outputs = model(adv_images)

            cost = self.criterion(outputs, labels).to(device)

            grad = torch.autograd.grad(
                cost, adv_images, retain_graph=False, create_graph=False
            )[0]

            adv_images = adv_images.detach() + self.alpha * grad.sign()
            delta = torch.clamp(adv_images - images, min=-eps, max=eps)
            adv_images = torch.clamp(images + delta, min=0, max=1).detach()

        return adv_images
