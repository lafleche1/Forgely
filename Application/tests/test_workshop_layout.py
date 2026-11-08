import unittest
from PIL import Image, ImageDraw
from forgely_atelier import workshop_visual_fallback, crop_zone


def workshop_scene():
    image = Image.new('RGB', (1648, 928), '#171717')
    draw = ImageDraw.Draw(image)
    purple = (60, 50, 90)
    draw.rectangle((274, 137, 1005, 174), fill=purple)
    draw.rectangle((277, 247, 476, 729), fill=purple)
    draw.rectangle((470, 175, 848, 747), fill=purple)
    draw.rectangle((811, 251, 985, 350), fill=purple)
    for y in (.275, .345, .415):
        cy = round(y * image.height)
        draw.rectangle((565, cy-8, 825, cy+8), fill=(30, 25, 50))
    draw.text((550, 142), 'JOAILLOMAGER', fill='white')
    draw.text((630, 282), '40 Force', fill=(80, 200, 90))
    draw.text((630, 440), '290 Vitalite', fill=(80, 200, 90))
    return image


class WorkshopLayoutTests(unittest.TestCase):
    def test_real_structure_is_required_and_survives_mask(self):
        from forgely_atelier import focus_workshop
        image = workshop_scene()
        self.assertTrue(workshop_visual_fallback(image))
        self.assertTrue(workshop_visual_fallback(focus_workshop(image)))

    def test_translated_and_scaled_workshop_is_reacquired(self):
        from forgely_workshop_layout import WorkshopLocator
        scene = workshop_scene()
        locator = WorkshopLocator()
        for scale, dx, dy in ((1., 180, 50), (.8, 260, 110), (1.1, -100, -40)):
            with self.subTest(scale=scale):
                moved = scene.transform(scene.size, Image.Transform.AFFINE,
                    (1/scale, 0, -dx/scale, 0, 1/scale, -dy/scale))
                result = locator.normalize(moved, context=str(scale))
                self.assertTrue(workshop_visual_fallback(result))
                self.assertEqual(result.size, scene.size)
                self.assertTrue(locator.verified)

    def test_closed_workshop_does_not_keep_previous_normalization(self):
        from forgely_workshop_layout import WorkshopLocator
        locator = WorkshopLocator()
        self.assertTrue(workshop_visual_fallback(locator.normalize(workshop_scene())))
        result = locator.normalize(Image.new('RGB', (1648, 928), (60, 50, 90)))
        self.assertFalse(locator.verified)
        self.assertFalse(workshop_visual_fallback(result))


if __name__ == '__main__':
    unittest.main()
