import torch

from src.utils.args import get_args
from src.utils.logger import get_logger
from src.utils.utils import get_lr, get_model, mask_check

args = get_args()

device = 'cuda' if torch.cuda.is_available() else 'cpu'
logger = get_logger(__name__)

cifar_10_classes = ('plane', 'car', 'bird', 'cat',
                    'deer', 'dog', 'frog', 'horse', 'ship', 'truck')


def test(testloader,
         model,
         criterion):
  model.eval()
  test_loss = 0
  correct = 0
  total = 0
  with torch.no_grad():
    for batch_idx, (inputs, targets) in enumerate(testloader):
      inputs, targets = inputs.to(device), targets.to(device)
      outputs = model(inputs)
      loss = criterion(outputs, targets)

      test_loss += loss.item()
      _, predicted = outputs.max(1)
      total += targets.size(0)
      correct += predicted.eq(targets).sum().item()

  acc = 100. * correct / total

  model.train()
  return loss, acc


# Training
def train(trainloader,
          testloader):
  # Get model, optimizer, criterion, lr_scheduler
  model, criterion, optimizer, lr_scheduler = get_model()
  model.train()
  if args.steps is None:
    steps = args.epochs * len(trainloader)

  logger.info('Mask check before training')
  mask_check(model)

  train_loss = 0
  correct = 0
  total = 0
  n_epochs = 0
  iterator = iter(trainloader)

  for batch_idx in range(0, steps, 1):
    step = batch_idx
    if batch_idx == n_epochs * len(trainloader):
      n_epochs = n_epochs + 1
      iterator = iter(trainloader)

    inputs, targets = iterator.next()
    inputs, targets = inputs.to(args.device), targets.to(args.device)
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()

    optimizer.step()
    lr_scheduler.step()
    train_loss += loss.item()

    _, predicted = outputs.max(1)
    total += targets.size(0)
    correct += predicted.eq(targets).sum().item()

    if batch_idx % args.eval_step == 0:
      string = ("Step {} Train Loss: {:.4f} "
                "Train Accuracy: {:.4f} Learning Rate {:.4f} ".format(step,
                                                                      loss,
                                                                      (correct / total),
                                                                      get_lr(optimizer)))
      logger.info(string)
      test_loss, test_acc = test(testloader, model, criterion)
      logger.info("Test Loss: {:.4f} Test Accuracy: {:.4f}".format(test_loss,
                                                                   test_acc))

  logger.info('Training completed')
  test_loss, test_acc = test(testloader, model, criterion)
  logger.info("Final Test Loss: {:.4f} Final Test Accuracy: {:.4f}".format(test_loss,
                                                                           test_acc))

  return model